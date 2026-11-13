"""Opt-in write-back of Python results to Snowflake ML.* tables (Power BI reads them through the PBI views).

Nothing is written unless the caller passes `enabled=True` or the environment sets FORECAST_WRITEBACK=1 (an explicit
`enabled=False` wins over the environment). Even then it only works on a Snowflake DataAccess wrapper. The entry point
that computes the three outputs and writes them is src/ml/publish_ml.py.

Tables (columns = the Power BI export files, see src/powerbi/model_spec.py FIXED_SCHEMAS, plus `run_id`):
    ML.FORECAST_BACKTEST, ML.LATE_DELIVERY_SCORES, ML.FLAG_SHARE

How a table is written (per call):
    1. CREATE TABLE IF NOT EXISTS (DDL, so it runs before the transaction);
    2. PUT the frame, as one Parquet file, into the user stage @~ under a fresh folder (retail_olist_ml/<run_id>/<nonce>/);
    3. BEGIN; DELETE ... WHERE run_id = ?; COPY INTO the table from that folder; COMMIT (ROLLBACK on any error);
    4. REMOVE the staged folder (also on failure) and delete the local temporary file.
Re-running with the same run_id therefore replaces that run's rows atomically, and rows of other run_ids are kept.
Never DROP, REPLACE, TRUNCATE or OVERWRITE.

Why the user stage: every user has one and may use it without any grant, whereas write_pandas creates a temporary stage
in the target schema, which needs CREATE STAGE on ML (granted to RETAIL_TRANSFORMER only since
06_model_registry_grants.sql, for the Model Registry; the write-back does not rely on it). COPY INTO <table> is DML, so
the delete and the load commit together.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

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
_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")  # becomes part of a stage path, so no quotes, slashes or spaces
STAGE_ROOT = "@~/retail_olist_ml"
# What new_run_id() makes. Consumers (the Power BI templates) take the text-greatest run_id as the latest run, which
# holds only for ids in this format: a hand-picked id such as "test" would sort above every timestamp for good.
GENERATED_RUN_ID = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def writeback_enabled(enabled: bool | None = None) -> bool:
    """Explicit argument wins; otherwise FORECAST_WRITEBACK=1 turns it on. Default off."""
    if enabled is not None:
        return bool(enabled)
    return os.environ.get("FORECAST_WRITEBACK", "").strip() == "1"


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
    out.columns = [c.upper() for c in out.columns]  # COPY matches them to the (unquoted, upper-case) table columns
    return out


def copy_sql(conn: DataAccess, table: str, stage_path: str, schema: str = ML_SCHEMA) -> str:
    """FORCE=TRUE: the load history must not skip a file because an identically named one was loaded before."""
    return (f"COPY INTO {_qualified(conn, table, schema)} FROM '{stage_path}' "
            "FILE_FORMAT = (TYPE = PARQUET) MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE ON_ERROR = ABORT_STATEMENT "
            "FORCE = TRUE PURGE = TRUE")


def _rows_loaded(cur) -> int:
    """Sum rows_loaded over the files in a COPY INTO result (one row per file)."""
    cols = [d[0].lower() for d in (cur.description or [])]
    if "rows_loaded" not in cols:
        raise DataAccessError(f"COPY INTO returned no rows_loaded column (columns: {cols})")
    i = cols.index("rows_loaded")
    return sum(int(r[i] or 0) for r in cur.fetchall())


def _load(conn: DataAccess, table: str, frame: pd.DataFrame, run_id: str, schema: str) -> int:
    folder = f"{STAGE_ROOT}/{run_id}/{uuid.uuid4().hex}"
    tmp = Path(tempfile.mkdtemp(prefix="retail_ml_"))
    cur = None
    staged = False
    try:  # from here on the temporary directory (it holds order-level data) is always removed
        local = tmp / f"{table.lower()}.parquet"
        uri = local.as_posix()
        if "'" in uri:  # PUT takes the path as a quoted literal; Snowflake documents no escape for a quote in it
            raise DataAccessError(f"temporary path {uri!r} contains a single quote, which PUT cannot take; "
                                  "set TMP/TEMP to a folder without one")
        frame.to_parquet(local, index=False)
        cur = conn.raw.cursor()
        staged = True  # from here a failed or partial PUT may have left files in the folder
        cur.execute(f"PUT 'file://{uri}' '{folder}/' AUTO_COMPRESS = FALSE")
        cur.execute("BEGIN")
        try:
            cur.execute(delete_sql(conn, table, schema), (run_id,))
            cur.execute(copy_sql(conn, table, f"{folder}/", schema))
            loaded = _rows_loaded(cur)
            if loaded != len(frame):
                raise DataAccessError(f"COPY INTO {table} loaded {loaded} rows, expected {len(frame)}")
            cur.execute("COMMIT")
        except BaseException:
            try:
                cur.execute("ROLLBACK")
            except Exception as exc:  # noqa: BLE001 - keep the original error; Snowflake rolls back on disconnect
                log.warning("ROLLBACK failed: %s", exc)
            raise
        return loaded
    finally:
        if cur is not None:
            if staged:
                try:
                    cur.execute(f"REMOVE '{folder}/'")  # PURGE already removed it after a successful load
                except Exception as exc:  # noqa: BLE001 - clean-up must not hide the real outcome
                    log.warning("could not remove staged files under %s: %s", folder, exc)
            cur.close()
        shutil.rmtree(tmp, ignore_errors=True)


def write_table(conn: DataAccess, table: str, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None,
                schema: str = ML_SCHEMA) -> int:
    """Create-if-missing, then atomically replace this run_id's rows with `df`. Returns rows written (0 when off)."""
    if table not in TABLE_COLUMNS:
        raise KeyError(f"unknown write-back table {table!r}; expected one of {', '.join(TABLE_COLUMNS)}")
    if not writeback_enabled(enabled):
        log.info("write-back to %s skipped (pass enabled=True or set FORECAST_WRITEBACK=1)", table)
        return 0
    if getattr(conn, "backend", None) != "snowflake":
        raise DataAccessError("write-back needs a Snowflake connection (DATA_BACKEND=snowflake).")
    if not isinstance(run_id, str) or not _RUN_ID.match(run_id):
        raise ValueError(f"run_id must be 1-100 letters, digits, '_' or '-' (got {run_id!r})")
    frame = _prepare(table, df, run_id)  # validate before touching Snowflake

    conn.execute(create_table_sql(conn, table, schema))
    return _load(conn, table, frame, run_id, schema)


def write_forecast_backtest(conn: DataAccess, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None) -> int:
    return write_table(conn, "FORECAST_BACKTEST", df, run_id, enabled=enabled)


def write_late_delivery_scores(conn: DataAccess, df: pd.DataFrame, run_id: str, *, enabled: bool | None = None) -> int:
    return write_table(conn, "LATE_DELIVERY_SCORES", df, run_id, enabled=enabled)


def write_flag_share(conn: DataAccess, run_id: str, flag_pcts: Iterable[int] = FLAG_SHARES, *,
                     enabled: bool | None = None) -> int:
    return write_table(conn, "FLAG_SHARE", pd.DataFrame({"flag_pct": list(flag_pcts)}), run_id, enabled=enabled)
