"""Named datasets for the Python modelling code, readable from either backend.

Tiers (which scripts can run against which backend):
  Tier 1, both backends, via these datasets:
      src/ml/forecast_baseline.py       -> weekly_series            (MARTS.mart_weekly_orders_revenue)
      src/ml/late_delivery_baseline.py  -> late_delivery_features   (MARTS.mart_late_delivery_features)
                                           unlabelled_share         (MARTS.fact_orders)
      src/ml/export_scores.py           -> build_from(con): late_delivery_features + order_category
                                           (INTERMEDIATE.int_late_delivery_item_agg); build(db) stays DuckDB-file based
  Tier 2, DuckDB only for now (they read warehouse tables directly with their own SQL, nothing here serves them):
      src/ml/drift_analysis.py, src/powerbi/export_data.py (except forecast_backtest), src/analytics/run_analytics.py

DuckDB path: the SQL below is the existing SQL, unchanged (late_delivery_features reads sql/ml/late_delivery_features.sql
itself); tests assert it returns exactly what the functions in src/ml return. Snowflake path: a plain read of the dbt
marts with an explicit ORDER BY that matches the DuckDB ordering (several consumers depend on row order, e.g. the stable
argsort in top_share_metrics and rank(method="first") in export_scores).

Each function returns the raw, SQL-equivalent frame (weekly_series keeps `week` as a column; src/ml applies its own
index/period post-processing on both paths) and validates it against the dataset schema.

Schemas are {column: kind} derived from the DuckDB output (kinds: str, int, float, bool, datetime; see normalise.py).
`float` accepts any numeric dtype, `int` needs an integer dtype, `datetime` is any datetime64 unit.
tests/test_data_access.py re-derives the column lists from the DuckDB SQL and fails if they drift.

The Snowflake queries read the prod marts built by `dbt build` (live run 2026-11-12; the marts reconcile with DuckDB, 22/22).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path

import pandas as pd
from pandas.api import types as pt

from .backend import DataAccess, DataAccessError, is_data_access, wrap_duckdb
from .normalise import KINDS, conform_frame, normalise_frame  # noqa: F401  (normalise_frame re-exported)

ROOT = Path(__file__).resolve().parents[2]
FEATURES_SQL = ROOT / "sql" / "ml" / "late_delivery_features.sql"
DEFAULT_MARTS_SCHEMA = "MARTS"

WEEKLY_SERIES_SCHEMA: dict[str, str] = {"week": "datetime", "orders": "int", "revenue": "float"}

# max_volume_cm3 is an integer (nullable Int64) in the built warehouse but follows product_volume_cm3's column type, so
# it is declared `float` (any numeric dtype) rather than `int`.
LATE_DELIVERY_FEATURES_SCHEMA: dict[str, str] = {
    "order_id": "str", "purchase_ts": "datetime", "delivered_customer_ts": "datetime", "is_late": "int",
    "purchase_dow": "int", "purchase_hour": "int", "purchase_month": "int", "promised_days": "float",
    "item_count": "int", "items_price": "float", "items_freight": "float", "freight_ratio": "float",
    "n_sellers": "int", "total_weight_g": "float", "max_volume_cm3": "float", "max_item_freight": "float",
    "distance_km": "float", "customer_state": "str", "seller_state": "str", "same_state": "int",
    "max_installments": "int", "main_payment_type": "str", "seller_prior_n": "int",
    "seller_prior_late_rate": "float", "route_prior_n": "float", "route_prior_late": "float",
    "category_prior_n": "float", "category_prior_late": "float", "recent_n_28d": "float",
    "recent_late_28d": "float", "route_prior_days": "float", "recent_days_28d": "float",
}

UNLABELLED_SHARE_SCHEMA: dict[str, str] = {"ym": "str", "n": "int", "labelled": "int"}

_WEEKLY_SERIES_DUCKDB = """
        with orders as (
            select date_trunc('week', purchase_ts)::date as week, count(*) as orders
            from fact_orders group by 1
        ), revenue as (
            select date_trunc('week', o.purchase_ts)::date as week, sum(oi.price)::double as revenue
            from fact_order_items oi join fact_orders o using (order_id) group by 1
        )
        select week, orders, coalesce(revenue, 0) as revenue
        from orders left join revenue using (week)
        order by week
        """

_UNLABELLED_SHARE_DUCKDB = """select strftime(o.purchase_ts, '%Y-%m') ym, count(*) n,
                  count(*) filter (where o.order_status = 'delivered' and o.is_late is not null
                                   and not o.has_timestamp_anomaly) labelled
           from fact_orders o group by 1"""

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


class SchemaError(DataAccessError, ValueError):
    """A frame does not match the schema of the dataset it was read for."""


def _kind_ok(s: pd.Series, kind: str) -> bool:
    d = s.dtype
    if kind == "str":
        return pt.is_string_dtype(d) and not pt.is_bool_dtype(d) and not pt.is_numeric_dtype(d)
    if kind == "int":
        return pt.is_integer_dtype(d) and not pt.is_bool_dtype(d)
    if kind == "float":
        return pt.is_numeric_dtype(d) and not pt.is_bool_dtype(d)
    if kind == "bool":
        return pt.is_bool_dtype(d)
    if kind == "datetime":
        return pt.is_datetime64_any_dtype(d)
    raise ValueError(f"unknown schema kind {kind!r}; expected one of {KINDS}")


def validate_frame(df: pd.DataFrame, schema: Mapping[str, str], *, name: str = "frame",
                   allow_extra: bool = True) -> pd.DataFrame:
    """Raise SchemaError unless `df` has every schema column with a compatible dtype. Returns df for chaining."""
    problems = [f"missing column {c!r}" for c in schema if c not in df.columns]
    problems += [f"column {c!r} has dtype {df[c].dtype}, expected kind {k}"
                 for c, k in schema.items() if c in df.columns and not _kind_ok(df[c], k)]
    if not allow_extra:
        problems += [f"unexpected column {c!r}" for c in df.columns if c not in schema]
    if problems:
        raise SchemaError(f"{name} failed schema validation: " + "; ".join(problems))
    return df


def _conn(conn) -> DataAccess:
    return conn if is_data_access(conn) else wrap_duckdb(conn)


def _schema_ident(marts_schema: str) -> str:
    if not _IDENT.match(marts_schema):
        raise ValueError(f"invalid schema name {marts_schema!r}")
    return marts_schema


def weekly_series(conn, *, marts_schema: str = DEFAULT_MARTS_SCHEMA) -> pd.DataFrame:
    """Orders and revenue per ISO week (Monday start), ordered by week. `week` is a column."""
    conn = _conn(conn)
    if conn.backend == "duckdb":
        df = conn.read_sql(_WEEKLY_SERIES_DUCKDB)
    else:
        cols = ", ".join(WEEKLY_SERIES_SCHEMA)
        df = conform_frame(conn.read_sql(
            f"select {cols} from {_schema_ident(marts_schema)}.mart_weekly_orders_revenue order by week"),
            WEEKLY_SERIES_SCHEMA)
    return validate_frame(df, WEEKLY_SERIES_SCHEMA, name="weekly_series")


def late_delivery_features(conn, *, marts_schema: str = DEFAULT_MARTS_SCHEMA) -> pd.DataFrame:
    """One row per delivered order: the output of sql/ml/late_delivery_features.sql (ordered by purchase_ts, order_id)."""
    conn = _conn(conn)
    if conn.backend == "duckdb":
        df = conn.read_sql(FEATURES_SQL.read_text(encoding="utf-8"))
    else:
        cols = ", ".join(LATE_DELIVERY_FEATURES_SCHEMA)
        df = conform_frame(conn.read_sql(
            f"select {cols} from {_schema_ident(marts_schema)}.mart_late_delivery_features "
            "order by purchase_ts, order_id"), LATE_DELIVERY_FEATURES_SCHEMA)
    return validate_frame(df, LATE_DELIVERY_FEATURES_SCHEMA, name="late_delivery_features")


def unlabelled_share(conn, *, marts_schema: str = DEFAULT_MARTS_SCHEMA) -> dict[str, float]:
    """Share of each month's orders with no usable label, as {'YYYY-MM': share rounded to 4 places}."""
    conn = _conn(conn)
    if conn.backend == "duckdb":
        df = conn.read_sql(_UNLABELLED_SHARE_DUCKDB)
    else:
        df = conform_frame(conn.read_sql(
            "select to_char(o.purchase_ts, 'YYYY-MM') as ym, count(*) as n, "
            "sum(case when o.order_status = 'delivered' and o.is_late is not null "
            "and not o.has_timestamp_anomaly then 1 else 0 end) as labelled "
            f"from {_schema_ident(marts_schema)}.fact_orders o group by 1"), UNLABELLED_SHARE_SCHEMA)
    validate_frame(df, UNLABELLED_SHARE_SCHEMA, name="unlabelled_share")
    return {ym: round(1 - int(labelled) / int(n), 4) for ym, n, labelled in zip(df["ym"], df["n"], df["labelled"])}


ORDER_CATEGORY_SCHEMA: dict[str, str] = {"order_id": "str", "category": "str"}

# The category of each labelled order's most expensive item (ties -> alphabetically first), as in
# drift_analysis.KEYS_SQL and sql/ml/late_delivery_features.sql. Used by src/ml/export_scores.py for the risk roll-ups.
_ORDER_CATEGORY_DUCKDB = """
with pop as (
    select order_id from fact_orders
    where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
), it as (
    select oi.order_id, oi.price, p.product_category_name_english as category
    from fact_order_items oi
    join pop using (order_id)
    join dim_product p    on p.product_key = oi.product_key
    join dim_seller s     on s.seller_key = oi.seller_key
    join dim_geography cg on cg.geography_key = oi.customer_geography_key
)
select order_id, coalesce(first(category order by price desc, category), 'unknown') as category
from it group by order_id order by order_id
"""


def order_category(conn, *, intermediate_schema: str = "INTERMEDIATE") -> pd.DataFrame:
    """One row per labelled order with items: the category of its most expensive item (ordered by order_id).

    Snowflake reads the dbt model int_late_delivery_item_agg, which applies the same tie rule (DD-21)."""
    conn = _conn(conn)
    if conn.backend == "duckdb":
        df = conn.read_sql(_ORDER_CATEGORY_DUCKDB)
    else:
        df = conform_frame(conn.read_sql(
            "select order_id, coalesce(category, 'unknown') as category "
            f"from {_schema_ident(intermediate_schema)}.int_late_delivery_item_agg order by order_id"), ORDER_CATEGORY_SCHEMA)
    return validate_frame(df, ORDER_CATEGORY_SCHEMA, name="order_category")


DATASETS: dict[str, tuple[Mapping[str, str], Callable]] = {
    "weekly_series": (WEEKLY_SERIES_SCHEMA, weekly_series),
    "late_delivery_features": (LATE_DELIVERY_FEATURES_SCHEMA, late_delivery_features),
    "unlabelled_share": (UNLABELLED_SHARE_SCHEMA, unlabelled_share),
    "order_category": (ORDER_CATEGORY_SCHEMA, order_category),
}


def load_dataset(name: str, conn, **kwargs):
    """Look a dataset up by name (weekly_series, late_delivery_features, unlabelled_share)."""
    try:
        _, fn = DATASETS[name]
    except KeyError:
        raise KeyError(f"unknown dataset {name!r}; expected one of {', '.join(DATASETS)}") from None
    return fn(conn, **kwargs)
