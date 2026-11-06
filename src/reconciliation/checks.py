"""Registry of reconciliation checks: DuckDB reference SQL, Snowflake SQL, join keys and comparison rules.

Every check returns a result set that is joined on its natural ``keys`` and compared column by column.

DuckDB side
    Analytics and feature checks execute the *tracked files* (sql/analytics/NN_*.sql, sql/ml/late_delivery_features.sql)
    unchanged, so there is exactly one copy of the reference SQL. Dimension / fact / headline checks are small SELECTs
    over the built warehouse. ``mart_weekly_orders_revenue`` repeats the query in src/ml/forecast_baseline.py
    ``weekly_series`` (a test keeps the two identical).

Snowflake side
    SELECTs over the dbt marts in ``<database>.<prefix>MARTS``. Shared SQL is written once with the token ``{M}`` that
    expands to nothing for DuckDB and to ``RETAIL_OLIST.MARTS.`` (or the dev-prefixed schema) for Snowflake. UNVERIFIED:
    none of the Snowflake SQL has been executed against a live account; it was written to the dbt model contract.

Comparison modes (the contract): counts, keys, money (Decimal), booleans, strings, dates and timestamps compare exact;
doubles compare relative 1e-9 unless a column rule says otherwise: haversine ``distance_km`` absolute 1e-6, latitude and
longitude medians relative 1e-9, rates absolute 1e-9.

Surrogate keys (``customer_key`` ...) are compared in a separate section and never decide a check's status. Facts carry
the *natural* key of each dimension (``customer_unique_id``, ``product_id``, ...), resolved by a join, in the main
comparison, so a differently numbered surrogate key cannot hide or fake a value difference.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
REFERENCE_DIR = ROOT / "reports" / "analytics"

REL_DOUBLE = 1e-9
ABS_DISTANCE_KM = 1e-6
ABS_RATE = 1e-9
SENSITIVE_COLUMNS = frozenset({"review_comment_title", "review_comment_message"})  # customer free text: never echoed


@dataclass(frozen=True)
class ColumnRule:
    mode: str = "exact"  # exact | abs | rel
    tol: float = 0.0
    surrogate: bool = False  # compared in the separate surrogate-key section

    def __post_init__(self) -> None:
        if self.mode not in {"exact", "abs", "rel"}:
            raise ValueError(f"unknown comparison mode {self.mode!r}")


EXACT = ColumnRule()
REL = ColumnRule("rel", REL_DOUBLE)
SURROGATE = ColumnRule("exact", 0.0, surrogate=True)


def absolute(tol: float) -> ColumnRule:
    return ColumnRule("abs", tol)


@dataclass(frozen=True)
class TieBreak:
    """A place where DuckDB ``arg_max`` and Snowflake ``max_by`` may legitimately pick different tied values.

    ``candidates_sql`` returns (order_id, candidate) for *every tied maximum* of every order in the population; an order is
    ambiguous when it has more than one candidate.
    - ``direct_column``: output column carrying the pick; a mismatch is a *tie_break* only if both sides' values are
      among the order's tied candidates, otherwise it stays an unexplained mismatch.
    - ``cascade_columns``: output columns computed from the pick across *other* rows (running category totals). With
      ``cascade_row_level`` a row's mismatch is *downstream_of_tie_break* only if (a) the order is itself ambiguous, or
      (b) its category is a value tied in some ambiguous order (running totals are partitioned by that value) AND the two
      totals differ by at most the number of ambiguous orders (only flipped orders can move between totals);
      anything else stays unexplained. For aggregate rows (``cascade_row_level=False``) any ambiguous order suffices.
    """

    name: str
    candidates_sql: str  # shared template ({M})
    direct_column: str | None = None
    cascade_columns: tuple[str, ...] = ()
    cascade_row_level: bool = True


@dataclass(frozen=True)
class Expected:
    value: Decimal
    source: str


@dataclass(frozen=True)
class Check:
    name: str
    group: str  # dimension | fact | analytics | ml | headline
    description: str
    keys: tuple[str, ...]
    duckdb_sql: str
    snowflake_sql: str  # template: {M} expands to "<db>.<schema prefix>MARTS."
    rules: dict[str, ColumnRule] = field(default_factory=dict)
    reference_csv: str | None = None
    expected: dict[str, Expected] = field(default_factory=dict)  # metric -> documented constant (headline checks)
    tie_breaks: tuple[TieBreak, ...] = ()

    def rule_for(self, column: str) -> ColumnRule | None:
        return self.rules.get(column)

    @property
    def surrogate_columns(self) -> tuple[str, ...]:
        return tuple(c for c, r in self.rules.items() if r.surrogate)


# ------------------------------------------------------------------ rendering

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def render_duckdb(sql: str) -> str:
    return sql.replace("{M}", "")


def render_snowflake(sql: str, database: str = "RETAIL_OLIST", schema_prefix: str = "") -> str:
    """Fill the ``{M}`` token. ``schema_prefix`` is "" for prod or ``"<SUFFIX>_"`` for a dbt dev target."""
    if not _IDENT.match(database):
        raise ValueError(f"database {database!r} is not a plain identifier")
    if schema_prefix and not _IDENT.match(schema_prefix):
        raise ValueError(f"schema prefix {schema_prefix!r} is not a plain identifier")
    return sql.replace("{M}", f"{database}.{schema_prefix}MARTS.")


def _read(relative: str) -> str:
    return (SQL_DIR / relative).read_text(encoding="utf-8")


def _strip_semicolon(sql: str) -> str:
    return sql.strip().rstrip(";").rstrip()


def _shared(name: str, group: str, description: str, keys: Iterable[str], sql: str, **kw) -> Check:
    return Check(name=name, group=group, description=description, keys=tuple(keys), duckdb_sql=render_duckdb(sql),
                 snowflake_sql=sql, **kw)


# ------------------------------------------------------------------ dimensions and facts


def _dimension_checks() -> list[Check]:
    return [
        _shared(
            "dim_customer", "dimension", "One row per customer_unique_id (+ the -1 member).", ["customer_unique_id"],
            "select customer_unique_id, customer_key, customer_zip_code_prefix, customer_city, customer_state "
            "from {M}dim_customer",
            rules={"customer_key": SURROGATE},
        ),
        _shared(
            "dim_date", "dimension", "One row per calendar day (+ the -1 member); date_key is the yyyymmdd smart key.",
            ["date_key"],
            "select date_key, full_date, year, quarter, month, month_name, year_month, day_of_month, iso_week, "
            "day_of_week, day_name, is_weekend from {M}dim_date",
        ),
        _shared(
            "dim_geography", "dimension",
            "One row per zip prefix (+ the -1 member, keyed here as __UNKNOWN__). Medians compared relative 1e-9.",
            ["zip_key"],
            "select coalesce(zip_prefix, '__UNKNOWN__') as zip_key, geography_key, zip_prefix, city, state, latitude, "
            "longitude, n_source_points from {M}dim_geography",
            rules={"geography_key": SURROGATE, "latitude": REL, "longitude": REL},
        ),
        _shared(
            "dim_product", "dimension", "One row per product_id (+ the -1 member).", ["product_id"],
            "select product_id, product_key, product_category_name, product_category_name_english, "
            "product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, "
            "product_height_cm, product_width_cm, product_volume_cm3 from {M}dim_product",
            rules={"product_key": SURROGATE},
        ),
        _shared(
            "dim_seller", "dimension", "One row per seller_id (+ the -1 member).", ["seller_id"],
            "select seller_id, seller_key, seller_zip_code_prefix, seller_city, seller_state from {M}dim_seller",
            rules={"seller_key": SURROGATE},
        ),
    ]


def _fact_checks() -> list[Check]:
    return [
        _shared(
            "fact_orders", "fact", "One row per order. Customer and geography are compared by natural key.",
            ["order_id"],
            "select o.order_id, o.customer_id, o.order_status, c.customer_unique_id, g.zip_prefix as customer_zip_prefix, "
            "o.purchase_date_key, o.approved_date_key, o.carrier_date_key, o.delivered_customer_date_key, "
            "o.estimated_delivery_date_key, o.purchase_ts, o.approved_ts, o.carrier_ts, o.delivered_customer_ts, "
            "o.estimated_delivery_ts, o.item_count, o.items_price, o.items_freight, o.payment_count, o.payment_total, "
            "o.delivery_days, o.delivery_delay_days, o.is_late, o.has_timestamp_anomaly, "
            "o.customer_key, o.customer_geography_key "
            "from {M}fact_orders o "
            "left join {M}dim_customer c on c.customer_key = o.customer_key "
            "left join {M}dim_geography g on g.geography_key = o.customer_geography_key",
            rules={"customer_key": SURROGATE, "customer_geography_key": SURROGATE},
        ),
        _shared(
            "fact_order_items", "fact", "One row per (order_id, order_item_id). Dimensions compared by natural key.",
            ["order_id", "order_item_id"],
            "select f.order_id, f.order_item_id, f.order_status, c.customer_unique_id, p.product_id, s.seller_id, "
            "gc.zip_prefix as customer_zip_prefix, gs.zip_prefix as seller_zip_prefix, "
            "f.purchase_date_key, f.shipping_limit_date_key, f.price, f.freight_value, f.item_total_value, "
            "f.customer_key, f.product_key, f.seller_key, f.customer_geography_key, f.seller_geography_key "
            "from {M}fact_order_items f "
            "left join {M}dim_customer c on c.customer_key = f.customer_key "
            "left join {M}dim_product p on p.product_key = f.product_key "
            "left join {M}dim_seller s on s.seller_key = f.seller_key "
            "left join {M}dim_geography gc on gc.geography_key = f.customer_geography_key "
            "left join {M}dim_geography gs on gs.geography_key = f.seller_geography_key",
            rules={"customer_key": SURROGATE, "product_key": SURROGATE, "seller_key": SURROGATE,
                   "customer_geography_key": SURROGATE, "seller_geography_key": SURROGATE},
        ),
        _shared(
            "fact_payments", "fact", "One row per (order_id, payment_sequential).", ["order_id", "payment_sequential"],
            "select f.order_id, f.payment_sequential, c.customer_unique_id, f.purchase_date_key, f.payment_type, "
            "f.payment_installments, f.payment_value, f.customer_key "
            "from {M}fact_payments f left join {M}dim_customer c on c.customer_key = f.customer_key",
            rules={"customer_key": SURROGATE},
        ),
        _shared(
            "fact_reviews", "fact", "One row per (review_id, order_id). Comment text is compared but never echoed.",
            ["review_id", "order_id"],
            "select f.review_id, f.order_id, c.customer_unique_id, f.review_creation_date_key, "
            "f.review_answer_date_key, f.review_creation_ts, f.review_answer_ts, f.review_score, "
            "f.review_comment_title, f.review_comment_message, f.has_comment, f.is_latest_review_for_order, "
            "f.customer_key "
            "from {M}fact_reviews f left join {M}dim_customer c on c.customer_key = f.customer_key",
            rules={"customer_key": SURROGATE},
        ),
    ]


_ROW_COUNT_TABLES = ["dim_customer", "dim_date", "dim_geography", "dim_product", "dim_seller",
                     "fact_orders", "fact_order_items", "fact_payments", "fact_reviews"]
_DOC = "docs/MIGRATING_TO_CLOUD.md:171-172 (parity targets)"


def _row_count_check() -> Check:
    sql = "\nunion all ".join(f"select '{t}' as metric, count(*)::decimal(18,4) as value from {{M}}{t}"
                              for t in _ROW_COUNT_TABLES)
    return _shared(
        "row_counts", "headline", "Row count of every dimension and fact (documented parity targets for the facts).",
        ["metric"], sql,
        expected={
            "fact_orders": Expected(Decimal(99441), _DOC),
            "fact_order_items": Expected(Decimal(112650), _DOC),
            "fact_payments": Expected(Decimal(103886), _DOC),
            "fact_reviews": Expected(Decimal(99224), _DOC),
        },
    )


_NOT_NET = "order_status not in ('canceled', 'unavailable')"
_LABELLED = "order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly"

_HEADLINE_SQL = f"""
select 'net_revenue' as metric, sum(price)::decimal(18,4) as value
  from {{M}}fact_order_items where {_NOT_NET}
union all select 'net_orders', count(*)::decimal(18,4)
  from {{M}}fact_orders where {_NOT_NET} and item_count > 0
union all select 'late_orders', count(*)::decimal(18,4) from {{M}}fact_orders where is_late
union all select 'orders_without_items', count(*)::decimal(18,4) from {{M}}fact_orders where item_count = 0
union all select 'labelled_delivered_orders', count(*)::decimal(18,4) from {{M}}fact_orders where {_LABELLED}
union all select 'labelled_late_orders', count(*)::decimal(18,4) from {{M}}fact_orders where {_LABELLED} and is_late
union all select 'timestamp_anomaly_orders', count(*)::decimal(18,4) from {{M}}fact_orders where has_timestamp_anomaly
union all select 'one_time_customers', count(*)::decimal(18,4) from (
    select customer_key from {{M}}fact_orders
    where {_NOT_NET} and item_count > 0 and customer_key <> -1
    group by customer_key having count(*) = 1)
union all select 'repeat_base_customers', count(*)::decimal(18,4) from (
    select customer_key from {{M}}fact_orders
    where {_NOT_NET} and item_count > 0 and customer_key <> -1
    group by customer_key)
union all select 'one_time_customer_share_pct',
    round(100.0 * sum(case when n = 1 then 1 else 0 end)::double / count(*), 2)::decimal(18,4)
  from (select customer_key, count(*) as n from {{M}}fact_orders
        where {_NOT_NET} and item_count > 0 and customer_key <> -1 group by customer_key)
"""


def _headline_check() -> Check:
    return _shared(
        "headline_numbers", "headline",
        "Headline figures, three-way: DuckDB vs Snowflake vs the documented constant. Definitions: net = not canceled/"
        "unavailable (sql/analytics/01, 03, 07); late = fact_orders.is_late (sql/validation/checks.sql); labelled = "
        "delivered, is_late not null, no timestamp anomaly (Power BI is_labelled_delivery, ML population); one-time = "
        "customers with exactly one net order (sql/analytics/07).",
        ["metric"], _HEADLINE_SQL,
        expected={
            "net_revenue": Expected(Decimal("13494400.74"), "docs/MIGRATING_TO_CLOUD.md:171; "
                                    "docs/analytics/BUSINESS_INSIGHTS.md"),
            "net_orders": Expected(Decimal(98199), "docs/MIGRATING_TO_CLOUD.md:171"),
            "late_orders": Expected(Decimal(7827), "sql/validation/checks.sql 'late deliveries (EDA: 7827)'"),
            "orders_without_items": Expected(Decimal(775), "sql/validation/checks.sql 'orders without items (EDA: 775)'"),
            "labelled_delivered_orders": Expected(Decimal(96282), "docs/MIGRATING_TO_CLOUD.md:172"),
            "labelled_late_orders": Expected(Decimal(7823), "docs/MIGRATING_TO_CLOUD.md:172"),
            "one_time_customer_share_pct": Expected(Decimal("96.96"), "reports/analytics/07_repeat_customers.csv (row 1)"),
        },
    )


# ------------------------------------------------------------------ analytics marts

_ANALYTICS = [
    # (file stem, mart, keys, description)
    ("01_monthly_kpis", "mart_monthly_kpis", ["year_month"], "Monthly KPIs"),
    ("02_category_performance", "mart_category_performance", ["category"], "Category performance"),
    ("03_state_performance", "mart_state_performance", ["customer_state"], "Customer-state performance"),
    ("04_seller_concentration", "mart_seller_concentration", ["metric"], "Seller revenue concentration"),
    ("05_delivery_vs_reviews", "mart_delivery_vs_reviews", ["delay_group"], "Late delivery vs review score"),
    ("06_payments", "mart_payments", ["payment_type"], "Payment mix"),
    ("07_repeat_customers", "mart_repeat_customers", ["orders_placed"], "Repeat purchasing"),
    ("08_delivery_trend", "mart_delivery_trend", ["purchase_month"], "Delivery trend by purchase month"),
]


def _analytics_checks() -> list[Check]:
    out = []
    for stem, mart, keys, desc in _ANALYTICS:
        out.append(Check(
            name=mart, group="analytics",
            description=f"{desc}: Snowflake {mart} vs sql/analytics/{stem}.sql and reports/analytics/{stem}.csv.",
            keys=tuple(keys),
            duckdb_sql=_read(f"analytics/{stem}.sql"),
            snowflake_sql=f"select * from {{M}}{mart}",
            reference_csv=f"{stem}.csv",
        ))
    return out


# ------------------------------------------------------------------ ML feature table and weekly series

_FEATURE_INT_COLS = ["is_late", "purchase_dow", "purchase_hour", "purchase_month", "item_count", "n_sellers",
                     "total_weight_g", "max_installments", "same_state", "seller_prior_n", "route_prior_n",
                     "route_prior_late", "category_prior_n", "category_prior_late", "recent_n_28d", "recent_late_28d"]
_FEATURE_DECIMAL_COLS = ["items_price", "items_freight", "max_item_freight"]
_FEATURE_FLOAT_COLS = ["promised_days", "freight_ratio", "max_volume_cm3", "distance_km", "seller_prior_late_rate",
                       "route_prior_days", "recent_days_28d"]

_FEATURE_RULES = {"distance_km": absolute(ABS_DISTANCE_KM), "seller_prior_late_rate": absolute(ABS_RATE)}


def _feature_aggregate_sql(source: str) -> str:
    """One row of aggregates over the feature table. ``source`` is a table name or a parenthesised subquery."""
    parts = ["count(*) as n_rows", "min(purchase_ts) as min_purchase_ts", "max(purchase_ts) as max_purchase_ts",
             "min(delivered_customer_ts) as min_delivered_ts", "max(delivered_customer_ts) as max_delivered_ts",
             "count(distinct customer_state) as n_distinct_customer_state",
             "count(distinct seller_state) as n_distinct_seller_state",
             "count(distinct main_payment_type) as n_distinct_main_payment_type",
             "sum(case when main_payment_type = 'unknown' then 1 else 0 end) as n_main_payment_type_unknown",
             "max(distance_km) as max_distance_km", "min(distance_km) as min_distance_km",
             "avg(seller_prior_late_rate) as avg_seller_prior_late_rate"]
    for c in _FEATURE_INT_COLS + _FEATURE_DECIMAL_COLS + _FEATURE_FLOAT_COLS:
        parts.append(f"sum({c}) as sum_{c}")
        parts.append(f"count({c}) as n_{c}")
    return "select 'all' as scope,\n  " + ",\n  ".join(parts) + f"\nfrom {source}"


_PAYMENT_TIES = """
with pop as (select order_id from {M}fact_orders
             where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly),
mx as (select p.order_id, max(p.payment_value) as mp from {M}fact_payments p join pop on pop.order_id = p.order_id
       group by p.order_id),
tied as (select distinct p.order_id, p.payment_type as candidate
         from {M}fact_payments p join mx on mx.order_id = p.order_id and p.payment_value = mx.mp)
select order_id, candidate from tied
"""

_CATEGORY_TIES = """
with pop as (select order_id from {M}fact_orders
             where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly),
it as (select oi.order_id, oi.price, coalesce(p.product_category_name_english, 'unknown') as candidate
       from {M}fact_order_items oi
       join pop on pop.order_id = oi.order_id
       join {M}dim_product p on p.product_key = oi.product_key),
mx as (select order_id, max(price) as mp from it group by order_id),
tied as (select distinct it.order_id, it.candidate from it join mx on mx.order_id = it.order_id and it.price = mx.mp)
select order_id, candidate from tied
"""

_WEEKLY_DUCKDB = """
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


def _ml_checks() -> list[Check]:
    features_sql = _strip_semicolon(_read("ml/late_delivery_features.sql"))
    return [
        Check(
            name="mart_late_delivery_features", group="ml",
            description="Row-level diff of the late-delivery feature table vs sql/ml/late_delivery_features.sql. "
                        "arg_max / max_by tie-breaks (category, main_payment_type) are classified and counted, never hidden.",
            keys=("order_id",),
            duckdb_sql=features_sql,
            snowflake_sql="select * from {M}mart_late_delivery_features",
            rules=dict(_FEATURE_RULES),
            tie_breaks=(
                TieBreak("main_payment_type", _PAYMENT_TIES, direct_column="main_payment_type"),
                TieBreak("category", _CATEGORY_TIES, cascade_columns=("category_prior_n", "category_prior_late")),
            ),
        ),
        Check(
            name="mart_late_delivery_features_aggregates", group="ml",
            description="Per-column aggregates (row count, sums, non-null counts, extremes, distinct counts) of the "
                        "late-delivery feature table.",
            keys=("scope",),
            duckdb_sql=f"with f as (\n{features_sql}\n)\n" + _feature_aggregate_sql("f"),
            snowflake_sql=_feature_aggregate_sql("{M}mart_late_delivery_features"),
            rules={"max_distance_km": absolute(ABS_DISTANCE_KM), "min_distance_km": absolute(ABS_DISTANCE_KM),
                   "avg_seller_prior_late_rate": absolute(ABS_RATE)},
            tie_breaks=(TieBreak("category", _CATEGORY_TIES, cascade_columns=("sum_category_prior_n",
                                                                               "sum_category_prior_late"),
                                 cascade_row_level=False),),
        ),
        Check(
            name="mart_weekly_orders_revenue", group="ml",
            description="Weekly orders and revenue (ISO Monday weeks) vs src/ml/forecast_baseline.py weekly_series.",
            keys=("week",),
            duckdb_sql=_WEEKLY_DUCKDB,
            snowflake_sql="select week::date as week, orders, revenue from {M}mart_weekly_orders_revenue",
        ),
    ]


def all_checks() -> list[Check]:
    return (_dimension_checks() + _fact_checks() + [_row_count_check(), _headline_check()]
            + _analytics_checks() + _ml_checks())


def select_checks(names: Iterable[str] | None = None, groups: Iterable[str] | None = None) -> list[Check]:
    checks = all_checks()
    if names:
        wanted = list(names)
        unknown = [n for n in wanted if n not in {c.name for c in checks}]
        if unknown:
            raise KeyError("unknown check(s): " + ", ".join(unknown))
        checks = [c for c in checks if c.name in wanted]
    if groups:
        g = set(groups)
        checks = [c for c in checks if c.group in g]
    return checks
