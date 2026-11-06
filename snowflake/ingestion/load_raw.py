#!/usr/bin/env python3
"""Load the nine Olist CSV files into Snowflake RETAIL_OLIST.RAW (PUT to an internal stage, then COPY INTO).

STATUS: written and unit-tested OFFLINE with a fake connector only. Nothing in this file has been run
against a real Snowflake account (UNVERIFIED live). See docs/migration/INGESTION_RUNBOOK.md.

What it does, in order
  1. Resolves the data directory (--data-dir, then RETAIL_DATA_DIR, then ./data) and checks that all
     nine files exist. This happens BEFORE any connection is attempted.
  2. Computes, locally, each file's sha256 and its RECORD count with the Python csv module (not a
     line count: order_reviews has embedded newlines, ~104.7k physical lines but 99,224 records;
     product_category_name_translation.csv starts with a UTF-8 BOM). It also checks the header and the
     field count of every record.
  3. --dry-run stops here: it prints the exact SQL it would run and never connects.
  4. Otherwise: prints the resolved account/database/role/warehouse, refuses to continue without --yes,
     connects with key-pair auth (settings from environment variables only), and per table:
       - skips it when this file's sha256 already has a SUCCESS row in RAW.INGESTION_LOG
         (and the table still holds the logged number of rows);
       - otherwise PUTs the file (OVERWRITE=TRUE), runs a transforming COPY INTO, verifies that the
         RAW table row count equals the expected record count, and writes SUCCESS/FAILED to the log.
  --reload <table|all> does TRUNCATE + reload for those tables. Nothing here ever DROPs anything,
  and this script creates no database objects (run snowflake/setup/*.sql and ingestion/*.sql first).

Environment variables (names only; values are never printed or stored)
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY_PATH, SNOWFLAKE_PRIVATE_KEY_PASSPHRASE (optional),
  RETAIL_SF_ROLE (default RETAIL_LOADER for this script), RETAIL_SF_WAREHOUSE (default RETAIL_WH),
  RETAIL_SF_DATABASE (default RETAIL_OLIST), RETAIL_DATA_DIR.

Exit codes: 0 ok / dry-run ok, 1 load failure, 2 configuration or usage error (nothing was loaded).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence, TextIO

DATA_DIR_HINT = r"C:\Users\Student\GCP\data"
STAGE = "RAW.OLIST_STAGE"
FILE_FORMAT = "RAW.OLIST_CSV"
LOG_TABLE = "RAW.INGESTION_LOG"
META_COLUMNS = ("_loaded_at", "_source_file", "_source_row_number", "_batch_id")

DEFAULT_ROLE = "RETAIL_LOADER"
DEFAULT_WAREHOUSE = "RETAIL_WH"
DEFAULT_DATABASE = "RETAIL_OLIST"

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


class IngestError(Exception):
    """A problem the user can act on (printed without a traceback)."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class TableSpec:
    table: str  # RAW table name, upper case
    filename: str  # CSV file name inside the data directory
    columns: tuple[str, ...]  # CSV header names (as in the file)

    @property
    def key(self) -> str:
        return self.table.lower()

    @property
    def stage_prefix(self) -> str:
        return f"@{STAGE}/{self.key}/"

    @property
    def staged_name(self) -> str:
        return f"{self.filename}.gz"  # PUT ... AUTO_COMPRESS=TRUE appends .gz


TABLES: tuple[TableSpec, ...] = (
    TableSpec("CUSTOMERS", "olist_customers_dataset.csv",
              ("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state")),
    TableSpec("GEOLOCATION", "olist_geolocation_dataset.csv",
              ("geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city",
               "geolocation_state")),
    TableSpec("ORDER_ITEMS", "olist_order_items_dataset.csv",
              ("order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price",
               "freight_value")),
    TableSpec("ORDER_PAYMENTS", "olist_order_payments_dataset.csv",
              ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value")),
    TableSpec("ORDER_REVIEWS", "olist_order_reviews_dataset.csv",
              ("review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
               "review_creation_date", "review_answer_timestamp")),
    TableSpec("ORDERS", "olist_orders_dataset.csv",
              ("order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
               "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date")),
    TableSpec("PRODUCTS", "olist_products_dataset.csv",
              ("product_id", "product_category_name", "product_name_lenght", "product_description_lenght",
               "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm",
               "product_width_cm")),
    TableSpec("SELLERS", "olist_sellers_dataset.csv",
              ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state")),
    TableSpec("PRODUCT_CATEGORY_TRANSLATION", "product_category_name_translation.csv",
              ("product_category_name", "product_category_name_english")),
)
BY_KEY = {t.key: t for t in TABLES}


@dataclass(frozen=True)
class FileInfo:
    spec: TableSpec
    path: Path
    sha256: str
    records: int  # data records (header excluded), parsed with the csv module
    physical_lines: int  # newline count, informational only
    size_bytes: int


# --------------------------------------------------------------------------------------------
# Local file handling (no Snowflake involved)
# --------------------------------------------------------------------------------------------
def resolve_data_dir(cli_value: str | None, env: Mapping[str, str], cwd: Path | None = None) -> Path:
    """--data-dir, then RETAIL_DATA_DIR, then ./data. An explicitly given but missing directory is an error."""
    cwd = cwd or Path.cwd()
    if cli_value:
        source, candidate = "--data-dir", Path(cli_value)
    elif env.get("RETAIL_DATA_DIR"):
        source, candidate = "RETAIL_DATA_DIR", Path(env["RETAIL_DATA_DIR"])
    else:
        source, candidate = "./data", cwd / "data"
    if not candidate.is_dir():
        raise IngestError(
            f"Data directory not found ({source} -> {candidate}).\n"
            f"The Olist CSVs are git-ignored and are not in this repository. On the author's machine they are in\n"
            f"  {DATA_DIR_HINT}\n"
            f"Set RETAIL_DATA_DIR to the folder holding the nine CSV files, or pass --data-dir.",
            code=2,
        )
    return candidate


def check_files_exist(data_dir: Path, specs: Sequence[TableSpec] = TABLES) -> None:
    missing = [s.filename for s in specs if not (data_dir / s.filename).is_file()]
    if missing:
        raise IngestError(
            f"Missing {len(missing)} expected file(s) in {data_dir}:\n  " + "\n  ".join(missing)
            + "\nNothing was loaded and no connection was attempted.",
            code=2,
        )


def sha256_and_lines(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    newlines = 0
    size = 0
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            newlines += chunk.count(b"\n")
            size += len(chunk)
    return digest.hexdigest(), newlines, size


def count_records(path: Path, expected_columns: Sequence[str]) -> int:
    """Number of data records, using csv parsing (quoted embedded newlines are NOT extra records).

    Reads with utf-8-sig so a leading BOM is not part of the first header name. Raises IngestError when
    the header differs from the expected columns or any record has the wrong number of fields (Snowflake
    would reject the same file with ERROR_ON_COLUMN_COUNT_MISMATCH).
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                raise IngestError(f"{path.name}: file is empty (no header row).", code=2) from None
            if tuple(header) != tuple(expected_columns):
                raise IngestError(
                    f"{path.name}: header {header} does not match the expected columns {list(expected_columns)}. "
                    f"Update TABLES in load_raw.py, ddl_raw.sql and the dbt sources together.",
                    code=2,
                )
            width = len(expected_columns)
            count = 0
            for row in reader:
                count += 1
                if len(row) != width:
                    raise IngestError(
                        f"{path.name}: record {count} has {len(row)} fields, expected {width}.", code=2)
    except UnicodeDecodeError as exc:
        raise IngestError(f"{path.name}: not valid UTF-8 ({exc}).", code=2) from None
    except csv.Error as exc:
        raise IngestError(f"{path.name}: CSV parse error ({exc}).", code=2) from None
    return count


def describe_files(data_dir: Path, specs: Sequence[TableSpec], out: TextIO) -> list[FileInfo]:
    infos = []
    for spec in specs:
        path = data_dir / spec.filename
        sha, lines, size = sha256_and_lines(path)
        records = count_records(path, spec.columns)
        infos.append(FileInfo(spec, path, sha, records, lines, size))
        print(f"  {spec.table:<30} {records:>10,} records  {lines:>10,} lines  sha256={sha[:16]}...", file=out)
    return infos


# --------------------------------------------------------------------------------------------
# SQL builders (pure functions; the dry-run prints exactly these strings)
# --------------------------------------------------------------------------------------------
def sql_str(value: str) -> str:
    """Single-quoted Snowflake string literal (backslash and quote escaped)."""
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def ident(value: str) -> str:
    if not _IDENT.match(value):
        raise IngestError(f"Refusing unsafe Snowflake identifier: {value!r}", code=2)
    return value


def put_uri(path: Path) -> str:
    """file:// URI with forward slashes: file://C:/Users/... on Windows, file:///home/... on POSIX."""
    posix = path.resolve().as_posix()
    if "'" in posix:
        raise IngestError(f"Refusing path containing a single quote: {posix}", code=2)
    return "file://" + posix


def sql_put(info: FileInfo) -> str:
    return (f"PUT '{put_uri(info.path)}' {info.spec.stage_prefix} "
            f"AUTO_COMPRESS = TRUE OVERWRITE = TRUE")


def sql_truncate(spec: TableSpec) -> str:
    return f"TRUNCATE TABLE RAW.{spec.table}"


def sql_copy(spec: TableSpec, batch_id: str, force: bool = False) -> str:
    targets = ", ".join(list(spec.columns) + list(META_COLUMNS))
    positional = ", ".join(f"${i}" for i in range(1, len(spec.columns) + 1))
    select = (f"{positional}, CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, METADATA$FILENAME, "
              f"METADATA$FILE_ROW_NUMBER, {sql_str(batch_id)}")
    lines = [
        f"COPY INTO RAW.{spec.table} ({targets})",
        f"FROM (SELECT {select} FROM {spec.stage_prefix})",
        f"FILES = ({sql_str(spec.staged_name)})",
        f"FILE_FORMAT = (FORMAT_NAME = {sql_str(FILE_FORMAT)})",
        "ON_ERROR = ABORT_STATEMENT",
    ]
    if force:
        lines.append("FORCE = TRUE")
    return "\n".join(lines)


def sql_count(spec: TableSpec) -> str:
    return f"SELECT COUNT(*) FROM RAW.{spec.table}"


def sql_log_lookup(info: FileInfo) -> str:
    return (f"SELECT COUNT(*), MAX(loaded_rows) FROM {LOG_TABLE} WHERE table_name = {sql_str(info.spec.table)} "
            f"AND sha256 = {sql_str(info.sha256)} AND status = 'SUCCESS'")


def sql_log_insert(info: FileInfo, batch_id: str, loaded_rows: int | None, status: str) -> str:
    loaded = "NULL" if loaded_rows is None else str(int(loaded_rows))
    return (f"INSERT INTO {LOG_TABLE} (batch_id, table_name, file_name, sha256, expected_rows, loaded_rows, "
            f"loaded_at, status) SELECT {sql_str(batch_id)}, {sql_str(info.spec.table)}, "
            f"{sql_str(info.spec.filename)}, {sql_str(info.sha256)}, {info.records}, {loaded}, "
            f"CURRENT_TIMESTAMP()::TIMESTAMP_NTZ, {sql_str(status)}")


# --------------------------------------------------------------------------------------------
# Snowflake execution
# --------------------------------------------------------------------------------------------
class Executor:
    """Thin wrapper over a DB-API connection: runs one statement, returns all rows, echoes the SQL."""

    def __init__(self, conn, out: TextIO):
        self.conn = conn
        self.out = out

    def run(self, sql: str) -> list[tuple]:
        print(f"  SQL> {sql.splitlines()[0]}{' ...' if len(sql.splitlines()) > 1 else ''}", file=self.out)
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:  # noqa: BLE001 - closing is best effort
                pass
        return list(rows) if rows is not None else []

    def scalar(self, sql: str) -> int:
        rows = self.run(sql)
        return int(rows[0][0]) if rows and rows[0] and rows[0][0] is not None else 0


def _check_put_result(rows: list[tuple]) -> None:
    # PUT result columns: source, target, source_size, target_size, source_compression,
    # target_compression, status, message.  Live behaviour UNVERIFIED.
    if not rows:
        raise IngestError("PUT returned no result rows.")
    for row in rows:
        status = str(row[6]).upper() if len(row) > 6 else ""
        if status and status not in {"UPLOADED", "SKIPPED"}:
            raise IngestError(f"PUT status {status}: {row[7] if len(row) > 7 else ''}")


def load_table(ex: Executor, info: FileInfo, batch_id: str, reload: bool) -> str:
    """Load one table. Returns 'LOADED', 'RELOADED' or 'SKIPPED'. Raises IngestError on failure."""
    spec = info.spec
    if not reload:
        logged = ex.run(sql_log_lookup(info))
        already = int(logged[0][0]) if logged and logged[0] and logged[0][0] is not None else 0
        current = ex.scalar(sql_count(spec))
        if already > 0:
            if current == info.records:
                return "SKIPPED"
            raise IngestError(
                f"{spec.table}: the log has a SUCCESS for this exact file but the table holds {current:,} rows "
                f"(expected {info.records:,}). Something changed the table; fix with --reload {spec.key}.")
        if current > 0:
            raise IngestError(
                f"{spec.table}: table already holds {current:,} rows but this file's sha256 has no SUCCESS in "
                f"{LOG_TABLE} (the file changed, or an earlier load was not logged). Refusing to append; "
                f"use --reload {spec.key} to TRUNCATE and reload.")
    loaded: int | None = None
    try:
        _check_put_result(ex.run(sql_put(info)))
        if reload:
            ex.run(sql_truncate(spec))
        ex.run(sql_copy(spec, batch_id, force=reload))
        loaded = ex.scalar(sql_count(spec))
    except Exception as exc:  # noqa: BLE001 - log the failure then re-raise as IngestError
        _log_best_effort(ex, info, batch_id, loaded, "FAILED")
        raise IngestError(f"{spec.table}: load failed ({type(exc).__name__}: {exc}). "
                          f"The load is a single COPY with ON_ERROR=ABORT_STATEMENT, so nothing from it was "
                          f"committed; fix the cause and re-run (use --reload {spec.key} if the table is not empty)."
                          ) from exc
    if loaded != info.records:
        _log_best_effort(ex, info, batch_id, loaded, "FAILED")
        raise IngestError(
            f"{spec.table}: row count mismatch, RAW has {loaded:,} rows, the CSV has {info.records:,} records. "
            f"Logged as FAILED. Investigate, then --reload {spec.key}.")
    ex.run(sql_log_insert(info, batch_id, loaded, "SUCCESS"))
    return "RELOADED" if reload else "LOADED"


def _log_best_effort(ex: Executor, info: FileInfo, batch_id: str, loaded: int | None, status: str) -> None:
    try:
        ex.run(sql_log_insert(info, batch_id, loaded, status))
    except Exception as exc:  # noqa: BLE001
        print(f"  WARNING: could not write {status} row to {LOG_TABLE}: {type(exc).__name__}", file=ex.out)


# --------------------------------------------------------------------------------------------
# Configuration / CLI
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class SnowflakeConfig:
    account: str
    user: str
    private_key_path: str
    passphrase: str | None
    role: str
    warehouse: str
    database: str


def resolve_config(env: Mapping[str, str], role: str | None, warehouse: str | None, database: str | None
                   ) -> SnowflakeConfig:
    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise IngestError(
            "Missing environment variable(s): " + ", ".join(missing)
            + ".\nSet them in your shell (never in a committed file). Nothing was loaded; no connection attempted.",
            code=2)
    key_path = env["SNOWFLAKE_PRIVATE_KEY_PATH"]
    if not Path(key_path).is_file():
        raise IngestError("SNOWFLAKE_PRIVATE_KEY_PATH does not point to an existing file.", code=2)
    return SnowflakeConfig(
        account=env["SNOWFLAKE_ACCOUNT"],
        user=env["SNOWFLAKE_USER"],
        private_key_path=key_path,
        passphrase=env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") or None,
        role=ident(role or env.get("RETAIL_SF_ROLE") or DEFAULT_ROLE),
        warehouse=ident(warehouse or env.get("RETAIL_SF_WAREHOUSE") or DEFAULT_WAREHOUSE),
        database=ident(database or env.get("RETAIL_SF_DATABASE") or DEFAULT_DATABASE),
    )


def default_connect(cfg: SnowflakeConfig, batch_id: str):
    try:
        import snowflake.connector  # type: ignore[import-not-found]
    except ImportError:
        raise IngestError(
            "snowflake-connector-python is not installed. Install it with\n"
            "  .\\.venv\\Scripts\\python.exe -m pip install \"snowflake-connector-python[pandas]\"\n"
            "(or `uv sync --extra snowflake` once the root environment is yours to rebuild).", code=2) from None
    kwargs = dict(
        account=cfg.account, user=cfg.user, private_key_file=cfg.private_key_path,
        role=cfg.role, warehouse=cfg.warehouse, database=cfg.database, schema="RAW",
        login_timeout=60, application="retail-olist-load-raw",
        session_parameters={"QUERY_TAG": f"retail_olist_load_raw:{batch_id}"},
    )
    if cfg.passphrase:
        kwargs["private_key_file_pwd"] = cfg.passphrase
    return snowflake.connector.connect(**kwargs)


def parse_table_list(value: str | None, flag: str) -> list[TableSpec] | None:
    """'all' -> every table; 'orders,sellers' -> those; None -> None."""
    if value is None:
        return None
    names = [n.strip().lower() for n in value.split(",") if n.strip()]
    if not names:
        raise IngestError(f"{flag}: empty table list.", code=2)
    if "all" in names:
        return list(TABLES)
    unknown = [n for n in names if n not in BY_KEY]
    if unknown:
        raise IngestError(f"{flag}: unknown table(s) {unknown}. Valid: all, " + ", ".join(BY_KEY), code=2)
    return [BY_KEY[n] for n in names]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="load_raw.py", description="Load the Olist CSVs into Snowflake RETAIL_OLIST.RAW.")
    p.add_argument("--data-dir", help="folder holding the nine CSVs (default: RETAIL_DATA_DIR, then ./data)")
    p.add_argument("--dry-run", action="store_true",
                   help="hash files, count records, print the exact SQL; never connect")
    p.add_argument("--yes", action="store_true", help="confirm the resolved account/role/warehouse/database")
    p.add_argument("--reload", metavar="TABLE|all", help="TRUNCATE + reload these tables (comma list or 'all')")
    p.add_argument("--only", metavar="TABLE,...", help="restrict the run to these tables")
    p.add_argument("--role", help="override RETAIL_SF_ROLE (default RETAIL_LOADER)")
    p.add_argument("--warehouse", help="override RETAIL_SF_WAREHOUSE (default RETAIL_WH)")
    p.add_argument("--database", help="override RETAIL_SF_DATABASE (default RETAIL_OLIST)")
    return p


def print_dry_run(infos: Sequence[FileInfo], reload_keys: set[str], batch_id: str, out: TextIO) -> None:
    print("\nDRY RUN: nothing is connected to or executed. The statements below are what a real run issues.", file=out)
    print("Decisions that need the live account (skip-if-already-loaded, non-empty-table guard) are shown as "
          "their lookup queries.", file=out)
    print(f"batch_id = {batch_id}", file=out)
    for info in infos:
        spec = info.spec
        reload = spec.key in reload_keys
        mode = "RELOAD (TRUNCATE + reload)" if reload else "normal"
        print(f"\n-- {spec.table}: {info.records:,} records, mode: {mode}", file=out)
        if not reload:
            print(sql_log_lookup(info) + ";   -- SUCCESS row for this sha256 => table is skipped", file=out)
            print(sql_count(spec) + ";   -- must equal logged rows (skip) or be 0 (first load)", file=out)
        print(sql_put(info) + ";", file=out)
        if reload:
            print(sql_truncate(spec) + ";", file=out)
        print(sql_copy(spec, batch_id, force=reload) + ";", file=out)
        print(sql_count(spec) + f";   -- must equal {info.records}", file=out)
        print(sql_log_insert(info, batch_id, info.records, "SUCCESS") + ";", file=out)


def main(argv: Sequence[str] | None = None, *, env: Mapping[str, str] | None = None,
         connect: Callable[[SnowflakeConfig, str], object] | None = None,
         out: TextIO | None = None, err: TextIO | None = None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    env = os.environ if env is None else env
    args = build_parser().parse_args(argv)
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    try:
        only = parse_table_list(args.only, "--only")
        reload_specs = parse_table_list(args.reload, "--reload") or []
        reload_keys = {s.key for s in reload_specs}
        specs = only if only is not None else list(TABLES)
        if only is not None:
            ignored = reload_keys - {s.key for s in specs}
            if ignored:
                raise IngestError(f"--reload names table(s) outside --only: {sorted(ignored)}", code=2)

        data_dir = resolve_data_dir(args.data_dir, env)
        check_files_exist(data_dir, specs)  # before any connection
        print(f"Data directory: {data_dir}", file=out)
        print("Local file facts (record counts via csv parsing, not line counts):", file=out)
        infos = describe_files(data_dir, specs, out)

        if args.dry_run:
            print_dry_run(infos, reload_keys, batch_id, out)
            return 0

        cfg = resolve_config(env, args.role, args.warehouse, args.database)
        print("\nResolved Snowflake target (credentials are not printed):", file=out)
        print(f"  account   : {cfg.account}", file=out)
        print(f"  database  : {cfg.database}", file=out)
        print(f"  role      : {cfg.role}", file=out)
        print(f"  warehouse : {cfg.warehouse}", file=out)
        print(f"  tables    : {', '.join(s.table for s in specs)}", file=out)
        if reload_keys:
            print(f"  RELOAD    : {', '.join(sorted(k.upper() for k in reload_keys))} "
                  f"(TRUNCATE then reload; no DROP)", file=out)
        if not args.yes:
            print("\nNot continuing: re-run with --yes to confirm this target. (Use --dry-run to only see the SQL.)",
                  file=out)
            return 2

        conn = (connect or default_connect)(cfg, batch_id)
        results: list[tuple[str, str]] = []
        try:
            ex = Executor(conn, out)
            print(f"\nbatch_id = {batch_id}", file=out)
            for info in infos:
                print(f"\n[{info.spec.table}]", file=out)
                outcome = load_table(ex, info, batch_id, info.spec.key in reload_keys)
                results.append((info.spec.table, outcome))
                print(f"  -> {outcome}", file=out)
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
        print("\nDone. " + ", ".join(f"{t}={o}" for t, o in results), file=out)
        return 0
    except IngestError as exc:
        print(f"\nERROR: {exc}", file=err)
        return exc.code
    except Exception as exc:  # noqa: BLE001 - connector / network errors: message only, no traceback dump
        print(f"\nERROR: {type(exc).__name__}: {exc}", file=err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
