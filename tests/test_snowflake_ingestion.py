"""Offline tests for snowflake/ingestion/load_raw.py and the Snowflake setup SQL files.

Nothing here connects to Snowflake: the connector is replaced by a fake that records the SQL it is given.
The fake proves the loader's own logic (record counting, ordering of statements, idempotency, guards).
It says nothing about how Snowflake itself behaves; that stays UNVERIFIED until a live run.
The real-CSV tests are skipped when the Olist data folder (git-ignored, not in the repo) is absent.
"""

from __future__ import annotations

import csv
import io
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INGESTION_DIR = ROOT / "snowflake" / "ingestion"
SETUP_DIR = ROOT / "snowflake" / "setup"
sys.path.insert(0, str(INGESTION_DIR))

import load_raw  # noqa: E402  (imported by path on purpose; "snowflake" is also the connector's package name)

REAL_DATA_DIR = Path(os.environ.get("RETAIL_DATA_DIR") or r"C:\Users\Student\GCP\data")
HAVE_REAL_DATA = all((REAL_DATA_DIR / t.filename).is_file() for t in load_raw.TABLES)
needs_real_data = pytest.mark.skipif(not HAVE_REAL_DATA, reason="Olist CSVs not available (git-ignored)")

SECRET_PASSPHRASE = "s3cr3t-passphrase-SENTINEL"
SECRET_KEY_BODY = "-----BEGIN PRIVATE KEY-----SENTINELKEYBODY-----END PRIVATE KEY-----"


# --------------------------------------------------------------------------------------------
# Fixtures and a fake Snowflake connector
# --------------------------------------------------------------------------------------------
def _write_csv(path: Path, columns, rows, bom=False):
    with open(path, "w", newline="", encoding="utf-8-sig" if bom else "utf-8") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        writer.writerow(columns)
        writer.writerows(rows)


@pytest.fixture()
def data_dir(tmp_path) -> Path:
    """Nine tiny CSVs with the real headers. Reviews has embedded newlines + doubled quotes."""
    folder = tmp_path / "data"
    folder.mkdir()
    for spec in load_raw.TABLES:
        n = len(spec.columns)
        if spec.table == "ORDER_REVIEWS":
            rows = [
                ["r1", "o1", "5", "", "line one\r\nline two\r\nline three", "2018-01-01 00:00:00", "2018-01-02 10:00:00"],
                ['r2', "o2", "1", 'T "quoted"', 'He said "no",\nand left', "2018-01-03 00:00:00", "2018-01-03 11:00:00"],
                ["r3", "o3", "4", "", "single line", "2018-01-04 00:00:00", "2018-01-05 12:00:00"],
            ]
        else:
            rows = [[f"{spec.key}_{i}_{j}" for j in range(n)] for i in range(4)]
        _write_csv(folder / spec.filename, spec.columns, rows, bom=(spec.table == "PRODUCT_CATEGORY_TRANSLATION"))
    return folder


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []

    def execute(self, sql):
        self.conn.executed.append(sql)
        self._rows = self.conn.respond(sql)

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeConnection:
    """Behaves like a tiny RAW schema: per-table row counts, an INGESTION_LOG, and COPY/PUT/TRUNCATE effects."""

    def __init__(self, expected_rows: dict[str, int], counts=None, success_log=None,
                 copy_loads=None, fail_on=None):
        self.expected_rows = expected_rows
        self.counts = dict(counts or {})
        self.success_log = set(success_log or [])  # {(TABLE, sha)}
        self.log_rows = []  # (table, status, loaded_rows)
        self.copy_loads = copy_loads or {}  # table -> rows COPY pretends to load
        self.fail_on = fail_on  # substring of SQL that raises
        self.executed: list[str] = []
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True

    def respond(self, sql):
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("simulated COPY failure")
        s = " ".join(sql.split())
        if s.startswith("SELECT COUNT(*), MAX(loaded_rows) FROM RAW.INGESTION_LOG"):
            table = re.search(r"table_name = '([^']+)'", s).group(1)
            sha = re.search(r"sha256 = '([^']+)'", s).group(1)
            hit = (table, sha) in self.success_log
            return [(1 if hit else 0, self.expected_rows[table] if hit else None)]
        m = re.match(r"SELECT COUNT\(\*\) FROM RAW\.(\w+)$", s)
        if m:
            return [(self.counts.get(m.group(1), 0),)]
        if s.startswith("PUT "):
            return [("src", "tgt", 1, 1, "NONE", "GZIP", "UPLOADED", "")]
        m = re.match(r"TRUNCATE TABLE RAW\.(\w+)$", s)
        if m:
            self.counts[m.group(1)] = 0
            return [("Statement executed successfully.",)]
        m = re.match(r"COPY INTO RAW\.(\w+)", s)
        if m:
            table = m.group(1)
            self.counts[table] = self.counts.get(table, 0) + self.copy_loads.get(table, self.expected_rows[table])
            return [("file", "LOADED", 1, 1, 1, 0, None, None, None, None)]
        if s.startswith("INSERT INTO RAW.INGESTION_LOG"):
            table = re.search(r"SELECT '[^']*', '([^']+)'", s).group(1)
            status = re.search(r", '(SUCCESS|FAILED)'$", s).group(1)
            loaded = re.search(r", (\d+|NULL), CURRENT_TIMESTAMP", s).group(1)
            self.log_rows.append((table, status, None if loaded == "NULL" else int(loaded)))
            sha = re.search(r"'([0-9a-f]{64})'", s).group(1)
            if status == "SUCCESS":
                self.success_log.add((table, sha))
            return [(1,)]
        raise AssertionError(f"unexpected SQL: {sql}")


def expected_rows_for(folder: Path) -> dict[str, int]:
    return {s.table: load_raw.count_records(folder / s.filename, s.columns) for s in load_raw.TABLES}


@pytest.fixture()
def key_file(tmp_path) -> Path:
    path = tmp_path / "rsa_key.p8"
    path.write_text(SECRET_KEY_BODY)
    return path


@pytest.fixture()
def env(data_dir, key_file) -> dict:
    return {
        "RETAIL_DATA_DIR": str(data_dir),
        "SNOWFLAKE_ACCOUNT": "acme-test123",
        "SNOWFLAKE_USER": "SOME_USER",
        "SNOWFLAKE_PRIVATE_KEY_PATH": str(key_file),
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": SECRET_PASSPHRASE,
    }


def run_main(argv, env, conn=None):
    out, err = io.StringIO(), io.StringIO()
    calls = []

    def connect(cfg, batch_id):
        calls.append(cfg)
        if conn is None:
            raise AssertionError("connect() must not be called in this scenario")
        return conn

    code = load_raw.main(argv, env=env, connect=connect, out=out, err=err)
    return code, out.getvalue(), err.getvalue(), calls


def sql_kinds(conn):
    return [" ".join(s.split())[:12] for s in conn.executed]


# --------------------------------------------------------------------------------------------
# Record counting, BOM, headers
# --------------------------------------------------------------------------------------------
def test_record_count_ignores_embedded_newlines(data_dir):
    spec = next(t for t in load_raw.TABLES if t.table == "ORDER_REVIEWS")
    path = data_dir / spec.filename
    assert load_raw.count_records(path, spec.columns) == 3
    _, physical_lines, _ = load_raw.sha256_and_lines(path)
    assert physical_lines > 4  # header + 3 records would be 4 lines; embedded newlines add more


def test_bom_header_is_stripped(data_dir):
    spec = next(t for t in load_raw.TABLES if t.table == "PRODUCT_CATEGORY_TRANSLATION")
    path = data_dir / spec.filename
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert load_raw.count_records(path, spec.columns) == 4  # would raise on a header mismatch if BOM leaked


def test_header_mismatch_and_short_record_are_rejected(tmp_path):
    bad_header = tmp_path / "a.csv"
    _write_csv(bad_header, ["x", "y"], [["1", "2"]])
    with pytest.raises(load_raw.IngestError, match="header"):
        load_raw.count_records(bad_header, ["a", "b"])
    short = tmp_path / "b.csv"
    short.write_bytes(b"a,b\r\n1,2\r\n3\r\n")
    with pytest.raises(load_raw.IngestError, match="record 2 has 1 fields"):
        load_raw.count_records(short, ["a", "b"])


def test_sha256_is_stable_and_content_sensitive(tmp_path):
    f = tmp_path / "x.csv"
    f.write_bytes(b"a,b\n1,2\n")
    sha1, _, size = load_raw.sha256_and_lines(f)
    assert len(sha1) == 64 and size == 8
    f.write_bytes(b"a,b\n1,3\n")
    assert load_raw.sha256_and_lines(f)[0] != sha1


@needs_real_data
def test_real_reviews_has_99224_records_not_line_count():
    spec = next(t for t in load_raw.TABLES if t.table == "ORDER_REVIEWS")
    path = REAL_DATA_DIR / spec.filename
    assert load_raw.count_records(path, spec.columns) == 99_224
    _, physical_lines, _ = load_raw.sha256_and_lines(path)
    assert physical_lines > 104_000  # ~104.7k physical lines: line counting would be wrong by ~5.5k


@needs_real_data
def test_real_files_record_counts_and_headers():
    expected = {
        "CUSTOMERS": 99_441, "GEOLOCATION": 1_000_163, "ORDER_ITEMS": 112_650, "ORDER_PAYMENTS": 103_886,
        "ORDER_REVIEWS": 99_224, "ORDERS": 99_441, "PRODUCTS": 32_951, "SELLERS": 3_095,
        "PRODUCT_CATEGORY_TRANSLATION": 71,
    }
    for spec in load_raw.TABLES:
        assert load_raw.count_records(REAL_DATA_DIR / spec.filename, spec.columns) == expected[spec.table], spec.table


# --------------------------------------------------------------------------------------------
# Data directory and file checks happen before connecting
# --------------------------------------------------------------------------------------------
def test_missing_file_fails_before_connecting(data_dir, env):
    (data_dir / "olist_sellers_dataset.csv").unlink()
    code, out, err, calls = run_main(["--yes"], env)
    assert code == 2 and calls == []
    assert "olist_sellers_dataset.csv" in err
    assert "no connection was attempted" in err


def test_missing_data_dir_names_the_expected_location(tmp_path, env):
    env = {**env, "RETAIL_DATA_DIR": str(tmp_path / "nope")}
    code, out, err, calls = run_main(["--dry-run"], env)
    assert code == 2 and calls == []
    assert r"C:\Users\Student\GCP\data" in err


def test_data_dir_precedence(tmp_path, monkeypatch):
    explicit, from_env, default = tmp_path / "e", tmp_path / "v", tmp_path / "data"
    for d in (explicit, from_env, default):
        d.mkdir()
    assert load_raw.resolve_data_dir(str(explicit), {"RETAIL_DATA_DIR": str(from_env)}, tmp_path) == explicit
    assert load_raw.resolve_data_dir(None, {"RETAIL_DATA_DIR": str(from_env)}, tmp_path) == from_env
    assert load_raw.resolve_data_dir(None, {}, tmp_path) == default


def test_missing_env_vars_fail_before_connecting(data_dir):
    code, out, err, calls = run_main(["--yes"], {"RETAIL_DATA_DIR": str(data_dir)})
    assert code == 2 and calls == []
    assert "SNOWFLAKE_ACCOUNT" in err and "SNOWFLAKE_USER" in err and "SNOWFLAKE_PRIVATE_KEY_PATH" in err


def test_requires_yes_and_prints_resolved_target(data_dir, env):
    code, out, err, calls = run_main([], env)
    assert code == 2 and calls == []
    for label in ("account", "database", "role", "warehouse"):
        assert label in out
    assert "acme-test123" in out and "RETAIL_OLIST" in out and "RETAIL_LOADER" in out and "RETAIL_WH" in out
    assert "--yes" in out


def test_role_warehouse_database_env_overrides(data_dir, env):
    env = {**env, "RETAIL_SF_ROLE": "RETAIL_TRANSFORMER", "RETAIL_SF_WAREHOUSE": "OTHER_WH",
           "RETAIL_SF_DATABASE": "OTHER_DB"}
    code, out, err, calls = run_main([], env)
    assert "RETAIL_TRANSFORMER" in out and "OTHER_WH" in out and "OTHER_DB" in out
    with pytest.raises(load_raw.IngestError):
        load_raw.resolve_config({**env, "RETAIL_SF_ROLE": "X; DROP"}, None, None, None)


# --------------------------------------------------------------------------------------------
# Dry run, secrets
# --------------------------------------------------------------------------------------------
def test_dry_run_emits_sql_and_never_connects_or_needs_credentials(data_dir):
    code, out, err, calls = run_main(["--dry-run"], {"RETAIL_DATA_DIR": str(data_dir)})
    assert code == 0 and calls == [] and err == ""
    assert "COPY INTO RAW.ORDER_REVIEWS" in out
    assert "METADATA$FILENAME" in out and "METADATA$FILE_ROW_NUMBER" in out and "CURRENT_TIMESTAMP()" in out
    assert "FILE_FORMAT = (FORMAT_NAME = 'RAW.OLIST_CSV')" in out
    assert "ON_ERROR = ABORT_STATEMENT" in out
    assert "OVERWRITE = TRUE" in out
    put_lines = [line for line in out.splitlines() if line.startswith("PUT ")]
    assert len(put_lines) == 9
    for line in put_lines:
        uri = re.search(r"'(file://[^']+)'", line).group(1)
        assert "\\" not in uri  # forward slashes only
    assert "DROP" not in out.upper().replace("DROPPED", "")
    assert "TRUNCATE" not in out  # no reload requested


def test_dry_run_reload_shows_truncate_and_force(data_dir):
    code, out, err, calls = run_main(["--dry-run", "--reload", "orders"], {"RETAIL_DATA_DIR": str(data_dir)})
    assert code == 0
    assert "TRUNCATE TABLE RAW.ORDERS" in out and "FORCE = TRUE" in out
    assert out.count("TRUNCATE TABLE") == 1


def test_put_uri_forward_slashes_on_this_platform(tmp_path):
    f = tmp_path / "dir with space" / "x.csv"
    f.parent.mkdir()
    f.write_text("a\n")
    info = load_raw.FileInfo(load_raw.TABLES[0], f, "0" * 64, 0, 1, 2)
    uri = load_raw.put_uri(f)
    assert uri.startswith("file://") and "\\" not in uri
    assert load_raw.sql_put(info).startswith("PUT 'file://")  # quoted, so spaces are safe


def test_sql_str_escapes_quotes_and_backslashes():
    assert load_raw.sql_str("a'b") == "'a''b'"
    assert load_raw.sql_str("a\\b") == "'a\\\\b'"


def test_no_secret_values_in_any_output(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    code, out, err, calls = run_main(["--yes"], env, conn)
    code2, out2, err2, _ = run_main([], env)  # without --yes
    code3, out3, err3, _ = run_main(["--dry-run"], env)
    everything = "\n".join([out, err, out2, err2, out3, err3] + conn.executed)
    assert SECRET_PASSPHRASE not in everything
    assert "SENTINELKEYBODY" not in everything
    assert code == 0 and code2 == 2 and code3 == 0
    cfg = calls[0]
    assert cfg.passphrase == SECRET_PASSPHRASE  # it is passed to the connector, just never printed


# --------------------------------------------------------------------------------------------
# Load flow against the fake connector
# --------------------------------------------------------------------------------------------
def test_first_load_runs_put_copy_verify_log_for_every_table(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    code, out, err, calls = run_main(["--yes"], env, conn)
    assert code == 0, err
    assert conn.closed
    for spec in load_raw.TABLES:
        mine = [s for s in conn.executed if f"RAW.{spec.table}" in s or spec.stage_prefix in s]
        put_i = next(i for i, s in enumerate(mine) if s.startswith("PUT "))
        copy_i = next(i for i, s in enumerate(mine) if s.startswith("COPY INTO"))
        assert put_i < copy_i
        assert not any(s.startswith("TRUNCATE") for s in mine)
        assert "FORCE" not in mine[copy_i]
    assert sorted(t for t, status, _ in conn.log_rows if status == "SUCCESS") == sorted(t.table for t in load_raw.TABLES)
    assert all(status == "SUCCESS" for _, status, _ in conn.log_rows)
    reviews_log = next(row for row in conn.log_rows if row[0] == "ORDER_REVIEWS")
    assert reviews_log[2] == 3  # record count, not physical line count


def test_rerun_with_unchanged_files_is_a_noop(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    assert run_main(["--yes"], env, conn)[0] == 0
    conn.executed.clear()
    log_before = list(conn.log_rows)
    code, out, err, _ = run_main(["--yes"], env, conn)
    assert code == 0, err
    assert not any(s.startswith(("PUT", "COPY", "TRUNCATE", "INSERT")) for s in conn.executed)
    assert conn.log_rows == log_before
    assert out.count("-> SKIPPED") == len(load_raw.TABLES)


def test_changed_file_into_nonempty_table_is_refused_not_appended(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    assert run_main(["--yes"], env, conn)[0] == 0
    conn.executed.clear()
    path = data_dir / "olist_customers_dataset.csv"
    path.write_bytes(path.read_bytes() + b"x,y,z,w,v\r\n")  # new content => new sha256, 1 more record
    conn.expected_rows["CUSTOMERS"] += 1
    code, out, err, _ = run_main(["--yes", "--only", "customers"], env, conn)
    assert code == 1
    assert "--reload customers" in err
    assert not any(s.startswith(("PUT", "COPY", "TRUNCATE")) for s in conn.executed)


def test_reload_truncates_after_put_and_never_drops(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    assert run_main(["--yes"], env, conn)[0] == 0
    conn.executed.clear()
    code, out, err, _ = run_main(["--yes", "--reload", "orders"], env, conn)
    assert code == 0, err
    truncs = [s for s in conn.executed if s.startswith("TRUNCATE")]
    assert truncs == ["TRUNCATE TABLE RAW.ORDERS"]
    assert not any("DROP" in s.upper() for s in conn.executed)
    order_stmts = [s for s in conn.executed if "RAW.ORDERS" in s or "orders/" in s]
    kinds = [s.split()[0] for s in order_stmts]
    assert kinds.index("PUT") < kinds.index("TRUNCATE") < kinds.index("COPY")
    assert "FORCE = TRUE" in next(s for s in conn.executed if s.startswith("COPY INTO RAW.ORDERS"))
    assert conn.counts["ORDERS"] == conn.expected_rows["ORDERS"]  # not doubled
    assert "RELOADED" in out
    # the other tables were skipped, untouched
    assert sum(1 for s in conn.executed if s.startswith("COPY")) == 1


def test_reload_all_truncates_every_table(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    assert run_main(["--yes"], env, conn)[0] == 0
    conn.executed.clear()
    assert run_main(["--yes", "--reload", "all"], env, conn)[0] == 0
    assert sum(1 for s in conn.executed if s.startswith("TRUNCATE")) == 9
    assert not any("DROP" in s.upper() for s in conn.executed)


def test_row_count_mismatch_is_logged_failed(data_dir, env):
    expected = expected_rows_for(data_dir)
    conn = FakeConnection(expected, copy_loads={"ORDERS": expected["ORDERS"] - 1})
    code, out, err, _ = run_main(["--yes", "--only", "orders"], env, conn)
    assert code == 1
    assert "mismatch" in err and "--reload orders" in err
    assert conn.log_rows == [("ORDERS", "FAILED", expected["ORDERS"] - 1)]


def test_copy_exception_is_logged_failed_and_stops(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir), fail_on="COPY INTO RAW.CUSTOMERS")
    code, out, err, _ = run_main(["--yes"], env, conn)
    assert code == 1
    assert "CUSTOMERS" in err and "simulated COPY failure" in err
    assert ("CUSTOMERS", "FAILED", None) in conn.log_rows
    assert conn.closed
    assert not any(s.startswith("COPY INTO RAW.GEOLOCATION") for s in conn.executed)  # stopped at first failure
    # recovery: fix the cause and re-run; tables that failed or never started are loaded, none duplicated
    conn.fail_on = None
    assert run_main(["--yes"], env, conn)[0] == 0
    assert all(conn.counts[t] == conn.expected_rows[t] for t in conn.expected_rows)


def test_skipped_table_with_drifted_rowcount_is_flagged(data_dir, env):
    conn = FakeConnection(expected_rows_for(data_dir))
    assert run_main(["--yes"], env, conn)[0] == 0
    conn.counts["SELLERS"] = 0  # someone emptied the table; the log still says SUCCESS
    code, out, err, _ = run_main(["--yes", "--only", "sellers"], env, conn)
    assert code == 1 and "--reload sellers" in err


def test_unknown_table_name_is_a_usage_error(data_dir, env):
    code, out, err, calls = run_main(["--dry-run", "--reload", "nonsense"], env)
    assert code == 2 and "unknown" in err


# --------------------------------------------------------------------------------------------
# SQL files
# --------------------------------------------------------------------------------------------
def _statements(path: Path) -> list[str]:
    text = "\n".join(line.split("--", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
    return [" ".join(s.split()) for s in text.split(";") if s.strip()]


def test_preflight_is_read_only():
    statements = _statements(SETUP_DIR / "00_preflight.sql")
    assert statements, "preflight must contain statements"
    forbidden = re.compile(r"\b(CREATE|ALTER|DROP|GRANT|REVOKE|INSERT|UPDATE|DELETE|MERGE|TRUNCATE|USE|SET|COPY|PUT|REMOVE|UNDROP|CALL|EXECUTE)\b", re.I)
    for stmt in statements:
        assert re.match(r"^(SHOW|SELECT)\b", stmt, re.I), stmt
        assert not forbidden.search(stmt), stmt
    joined = " ".join(statements).upper()
    for needle in ("SHOW DATABASES LIKE 'RETAIL%'", "SHOW WAREHOUSES LIKE 'RETAIL%'", "SHOW ROLES LIKE 'RETAIL%'",
                   "CURRENT_ACCOUNT()", "CURRENT_ROLE()", "CURRENT_USER()"):
        assert needle in joined


@pytest.mark.parametrize("name", ["01_objects.sql", "02_grants.sql"])
def test_setup_files_have_no_replace_or_drop_even_in_comments(name):
    text = (SETUP_DIR / name).read_text(encoding="utf-8").upper()
    assert "OR REPLACE" not in text
    assert not re.search(r"\bDROP\b", text)
    code = " ".join(_statements(SETUP_DIR / name)).upper()
    assert "RESOURCE MONITOR" not in code  # may be mentioned in a comment, never created
    assert "ACCOUNTADMIN" not in text  # no account-level role needed or used


def test_objects_sql_matches_the_contract():
    text = (SETUP_DIR / "01_objects.sql").read_text(encoding="utf-8")
    for schema in ("RAW", "STAGING", "INTERMEDIATE", "MARTS", "PBI", "ML"):
        assert f"CREATE SCHEMA IF NOT EXISTS RETAIL_OLIST.{schema}" in text
    assert "CREATE DATABASE IF NOT EXISTS RETAIL_OLIST" in text
    assert re.search(r"CREATE WAREHOUSE IF NOT EXISTS RETAIL_WH", text)
    for needle in ("WAREHOUSE_SIZE = 'XSMALL'", "AUTO_SUSPEND = 60", "AUTO_RESUME = TRUE", "INITIALLY_SUSPENDED = TRUE"):
        assert needle in text
    for role in ("RETAIL_LOADER", "RETAIL_TRANSFORMER", "RETAIL_REPORTER"):
        assert f"CREATE ROLE IF NOT EXISTS {role}" in text
    assert "SINGLE-ROLE FALLBACK" in text
    for line in _statements(SETUP_DIR / "01_objects.sql"):
        if line.upper().startswith("CREATE"):
            assert "IF NOT EXISTS" in line.upper(), line


def test_grants_include_future_grants_and_are_additive():
    stmts = _statements(SETUP_DIR / "02_grants.sql")
    assert all(re.match(r"^(GRANT|USE ROLE|SET)\b", s, re.I) for s in stmts), [s for s in stmts if not re.match(r"^(GRANT|USE ROLE|SET)\b", s, re.I)]
    text = " ".join(stmts).upper()
    assert "ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.RAW TO ROLE RETAIL_TRANSFORMER" in text
    assert "ON FUTURE VIEWS IN SCHEMA RETAIL_OLIST.PBI TO ROLE RETAIL_REPORTER" in text
    assert "ON FUTURE TABLES IN SCHEMA RETAIL_OLIST.ML TO ROLE RETAIL_REPORTER" in text
    assert "REVOKE" not in text
    # reporter never gets write privileges
    for s in stmts:
        if s.upper().endswith("TO ROLE RETAIL_REPORTER"):
            assert not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE)\b", s, re.I), s


def test_file_format_options():
    text = (INGESTION_DIR / "file_formats.sql").read_text(encoding="utf-8")
    code = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
    for needle in ("FIELD_OPTIONALLY_ENCLOSED_BY = '\"'", "SKIP_HEADER = 1", "ENCODING = 'UTF8'",
                   "SKIP_BYTE_ORDER_MARK = TRUE", "EMPTY_FIELD_AS_NULL = TRUE", "NULL_IF = ('')",
                   "ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE",
                   "ESCAPE_UNENCLOSED_FIELD = NONE"):
        assert needle in code, needle
    assert "CREATE FILE FORMAT IF NOT EXISTS RAW.OLIST_CSV" in code
    assert "CREATE STAGE IF NOT EXISTS RAW.OLIST_STAGE" in code
    assert not re.search(r"\b(OR REPLACE|DROP)\b", code, re.I)


def _ddl_tables() -> dict[str, list[tuple[str, str]]]:
    text = (INGESTION_DIR / "ddl_raw.sql").read_text(encoding="utf-8")
    tables = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS RAW\.(\w+) \((.*?)\n\)", text, re.S):
        cols = []
        for line in m.group(2).splitlines():
            line = line.split("--", 1)[0].strip().rstrip(",")
            if line:
                name, dtype = line.split(None, 1)
                cols.append((name, dtype))
        tables[m.group(1)] = cols
    return tables


def test_ddl_matches_loader_spec_and_contract():
    tables = _ddl_tables()
    assert set(tables) == {t.table for t in load_raw.TABLES} | {"INGESTION_LOG"}
    for spec in load_raw.TABLES:
        cols = tables[spec.table]
        names = [c for c, _ in cols]
        assert names == list(spec.columns) + list(load_raw.META_COLUMNS), spec.table
        source_types = {t for c, t in cols if c in spec.columns}
        assert source_types == {"VARCHAR"}, "all source columns must be VARCHAR"
    assert [c for c, _ in tables["INGESTION_LOG"]] == [
        "batch_id", "table_name", "file_name", "sha256", "expected_rows", "loaded_rows", "loaded_at", "status"]
    text = (INGESTION_DIR / "ddl_raw.sql").read_text(encoding="utf-8").upper()
    assert "OR REPLACE" not in text and not re.search(r"\bDROP\b", text)
    assert "PRODUCT_NAME_LENGHT" in text and "PRODUCT_DESCRIPTION_LENGHT" in text.replace("PRODUCT_DESCRIPTION_LENGHT", "PRODUCT_DESCRIPTION_LENGHT")


@needs_real_data
def test_loader_column_specs_match_real_csv_headers():
    for spec in load_raw.TABLES:
        with open(REAL_DATA_DIR / spec.filename, newline="", encoding="utf-8-sig") as handle:
            assert tuple(next(csv.reader(handle))) == spec.columns, spec.table


def test_generated_sql_uses_only_expected_statement_types(data_dir):
    infos = load_raw.describe_files(data_dir, load_raw.TABLES, io.StringIO())
    for info in infos:
        copy = load_raw.sql_copy(info.spec, "batch-1")
        assert copy.startswith(f"COPY INTO RAW.{info.spec.table} (")
        assert f"${len(info.spec.columns)}" in copy and f"${len(info.spec.columns) + 1}" not in copy
        assert "'batch-1'" in copy
        assert "FORCE" not in copy and "FORCE = TRUE" in load_raw.sql_copy(info.spec, "b", force=True)
        assert "DROP" not in load_raw.sql_truncate(info.spec).upper()

@pytest.mark.parametrize("name", ["rsa_key.p8", "snowflake_key.p8", "key.p12", "key.pfx", "id.pem", "id.key", ".env", ".env.local"])
def test_private_key_and_env_files_are_git_ignored(name):
    """Key-pair auth means a stray private key is the biggest leak risk: every usual key/env file name must be ignored."""
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "check-ignore", "-q", "--no-index", name], cwd=repo)
    assert result.returncode == 0, f"{name} is not covered by .gitignore"


def test_env_example_is_not_ignored():
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    assert subprocess.run(["git", "check-ignore", "-q", "--no-index", ".env.example"], cwd=repo).returncode == 1
