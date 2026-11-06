"""Opt-in write-back of Python results to Snowflake ML.* tables (Power BI reads them through the PBI views).

Nothing is written unless the caller passes `enabled=True` or the environment sets FORECAST_WRITEBACK=1 (an explicit
`enabled=False` wins over the environment). Even then it only works on a Snowflake DataAccess wrapper.

Tables (columns = the Power BI export files, see src/powerbi/model_spec.py FIXED_SCHEMAS, plus `run_id`):
    ML.FORECAST_BACKTEST, ML.LATE_DELIVERY_SCORES, ML.FLAG_SHARE

Statements issued, in order, per call: CREATE TABLE IF NOT EXISTS; DELETE ... WHERE run_id = ?; a write_pandas() append.
Never DROP, REPLACE, TRUNCATE or overwrite. Re-running with the same run_id therefore replaces that run's rows only, and
rows from other run_ids are kept. The delete and the insert are NOT one transaction (write_pandas creates a temporary
stage and file format, which are DDL and end any open transaction in Snowflake): if the insert fails after the delete,
re-run with the same run_id.

UNVERIFIED against a live account: nothing here has touched Snowflake. The tests use a fake connector and a fake
write_pandas.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime

import pandas as pd

from .backend import DataAccess, DataAccessError
from .datasets import validate_frame

log = logging.getLogger(__name__)

ML_SCHEMA = "ML"
FLAG_SHARES = (5, 10, 15, 20, 25, 30)  # same list as src/powerbi/export_data.py FLAG_SHARES

# name -> (column, snowflake type) in table order; run_id first.
TABLE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "FORECAST_BACKTEST": [
        ("run_id", "VARCHAR"), ("target", "VARCHAR"), ("horizon", "NUMBER(38,0)"), ("method", "VARCHAR"),
        ("target_week", "DATE"), ("forecast", "FLOAT"), ("actual", "FLOAT"), ("abs_error", "FLOAT"),
    ],
    "LATE_DELIVERY_SCORES": [
        ("run_id", "VARCHAR"), ("order_id", "VARCHAR"), ("month", "VARCHAR"), ("purchase_date_key", "NUMBER(38,0)"),
        ("risk_score", "FLOAT"), ("risk_percentile", "FLOAT"), ("flagged_top10", "BOOLEAN"),
        ("is_late", "NUMBER(38,0)"), ("customer_state", "VARCHAR"), ("seller_state", "VARCHAR"),
        ("category", "VARCHAR"), ("promised_days", "FLOAT"),
    ],
    "FLAG_SHARE": [("run_id", "VARCHAR"), ("flag_pct", "NUMBER(38,0)")],
}

# input-frame schemas (without run_id, which is added here)
SCHEMAS: dict[str, dict[str, str]] = {
    "FORECAST_BACKTEST": {"target": "str", "horizon": "int", "method": "str", "target_week": "datetime",
                          "forecast": "float", "actual": "float", "abs_error": "float"},
    "LATE_DELIVERY_SCORES": {"order_id": "str", "month": "str", "purchase_date_key": "int", "risk_score": "float",
                             "risk_percentile": "float", "flagged_top10": "bool", "is_late": "int",
                             "customer_state": "str", "seller_state": "str", "category": "str",
                             "promised_days": "float"},
    "FLAG_SHARE": {"flag_pct": "int"},
}

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def writeback_enabled(enabled: bool | None = None) -> bool:
    """Explicit argument wins; otherwise FORECAST_WRITEBACK=1 turns it on. Default off."""
    if enabled is not None:
        return bool(enabled)
    return os.environ.get("FORECAST_WRITEBACK", "").strip() == "1"


def _write_pandas():  # isolated so tests can substitute a fake
    from snowflake.connector.pandas_tools import write_pandas

    return write_pandas


def _qualified(conn: DataAccess, table: str, schema: str) -> str:
    if not _IDENT.match(schema):
        raise ValueError(f"invalid schema name {schema!r}")
    db = conn.target.database if conn.target is not None else None
    if db is not None and not _IDENT.match(db):
        raise ValueError(f"invalid database name {db!r}")
    return f"{db}.{schema}.{table}" if db else f"{schema}.{table}"


def create_table_sql(conn: DataAccess, table: str, schema: str = ML_SCHEMA) -> str:
    cols = ",\n    ".join(f"{name} {typ}" for name, typ in TABLE_COLUMNS[table])
    return f"CREATE TABLE IF NOT EXISTS {_qualified(conn, table, schema)} (\n    {cols}\n)"


def delete_sql(conn: DataAccess, table: str, schema: str = ML_SCHEMA) -> str:
    return f"DELETE FROM {_qualified(conn, table, schema)} WHERE run_id = ?"


def _prepare(table: str, df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    out = df.copy()
    if table == "FORECAST_BACKTEST" and "target_week" in out.columns:
        out["target_week"] = pd.to_datetime(out["target_week"])
    validate_frame(out, SCHEMAS[table], name=table)
    out = out[list(SCHEMAS[table])]
    if table == "FORECAST_BACKTEST":
        out["target_week"] = out["target_week"].dt.date  # DATE column
    out.insert(0, "run_id", run_id)
    out.columns = [c.upper() for c in out.columns]  # write_pandas(quote_identifiers=False) matches upper-case names
    return out


def write_table(conn: DataAccess, table: str, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None,
                schema: str = ML_SCHEMA) -> int:
    """Create-if-missing, delete this run_id's rows, append `df`. Returns rows written (0 when not enabled)."""
    if table not in TABLE_COLUMNS:
        raise KeyError(f"unknown write-back table {table!r}; expected one of {', '.join(TABLE_COLUMNS)}")
    if not writeback_enabled(enabled):
        log.info("write-back to %s skipped (pass enabled=True or set FORECAST_WRITEBACK=1)", table)
        return 0
    if getattr(conn, "backend", None) != "snowflake":
        raise DataAccessError("write-back needs a Snowflake connection (DATA_BACKEND=snowflake).")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    frame = _prepare(table, df, run_id)  # validate before touching Snowflake

    conn.execute(create_table_sql(conn, table, schema))
    conn.execute(delete_sql(conn, table, schema), [run_id])
    kwargs = {"database": conn.target.database} if conn.target is not None else {}
    ok, _chunks, nrows, *_ = _write_pandas()(
        conn.raw, frame, table, schema=schema, quote_identifiers=False, auto_create_table=False, overwrite=False,
        **kwargs)
    if not ok or nrows != len(frame):
        raise DataAccessError(f"write_pandas into {table} reported success={ok}, rows={nrows}, expected {len(frame)}")
    return int(nrows)


def write_forecast_backtest(conn: DataAccess, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None) -> int:
    return write_table(conn, "FORECAST_BACKTEST", df, run_id, enabled=enabled)


def write_late_delivery_scores(conn: DataAccess, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None) -> int:
    return write_table(conn, "LATE_DELIVERY_SCORES", df, run_id, enabled=enabled)


def write_flag_share(conn: DataAccess, run_id: str, flag_pcts: Iterable[int] = FLAG_SHARES, *,
                     enabled: bool | None = None) -> int:
    return write_table(conn, "FLAG_SHARE", pd.DataFrame({"flag_pct": list(flag_pcts)}), run_id, enabled=enabled)
