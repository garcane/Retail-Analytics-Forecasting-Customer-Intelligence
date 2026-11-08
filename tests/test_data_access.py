"""Offline tests for src/data_access: no network, no Snowflake. The connector, key loader and write_pandas are fakes."""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

import duckdb
import forecast_baseline as fb
import late_delivery_baseline as ldb
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from data_access import backend as be
from data_access import datasets, writeback
from data_access.datasets import (
    LATE_DELIVERY_FEATURES_SCHEMA,
    UNLABELLED_SHARE_SCHEMA,
    WEEKLY_SERIES_SCHEMA,
    SchemaError,
    validate_frame,
)
from data_access.normalise import conform_frame, normalise_frame

PASSPHRASE = "s3cret-passphrase-do-not-print"
ENV_NAMES = [
    "DATA_BACKEND", "DUCKDB_PATH", "RETAIL_SF_CONFIRM", "FORECAST_WRITEBACK", "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER",
    "SNOWFLAKE_PRIVATE_KEY_PATH", "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "RETAIL_SF_ROLE", "RETAIL_SF_WAREHOUSE",
    "RETAIL_SF_DATABASE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def sf_env(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct-xy12345")
    monkeypatch.setenv("SNOWFLAKE_USER", "someone")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PATH", "/nonexistent/key.p8")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", PASSPHRASE)


# -- fakes -------------------------------------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.description = None
        self._rows = []
        self._frame = None

    def execute(self, sql, params=None):
        self.conn.log.append((sql, params))
        self._frame = next((f for pat, f in self.conn.results if pat in sql), None)
        if self._frame is not None:
            self.description = [(c,) for c in self._frame.columns]
            self._rows = list(self._frame.itertuples(index=False, name=None))
        return self

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeCursorPandas(FakeCursor):
    def fetch_pandas_all(self):
        return self._frame.copy()


class FakeConn:
    def __init__(self, results=(), pandas_fetch=True):
        self.log = []
        self.results = list(results)
        self.cursor_cls = FakeCursorPandas if pandas_fetch else FakeCursor
        self.closed = False

    def cursor(self):
        return self.cursor_cls(self)

    def close(self):
        self.closed = True

    @property
    def sql(self):
        return [s for s, _ in self.log]


def sf_wrapper(results=(), pandas_fetch=True):
    target = be.SnowflakeTarget("acct", "RETAIL_OLIST", "RETAIL_TRANSFORMER", "RETAIL_WH")
    return be.DataAccess("snowflake", FakeConn(results, pandas_fetch), target=target)


# -- backend selection ---------------------------------------------------------------------------------------------


def test_default_backend_is_duckdb():
    assert be.resolve_backend() == "duckdb"


def test_invalid_backend_raises(monkeypatch):
    with pytest.raises(be.InvalidBackendError, match="postgres"):
        be.resolve_backend("postgres")
    monkeypatch.setenv("DATA_BACKEND", "bigquery")
    with pytest.raises(be.InvalidBackendError, match="bigquery"):
        be.connect()
    assert issubclass(be.InvalidBackendError, ValueError)


def test_env_switches_backend_and_argument_wins(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", " Snowflake ")
    assert be.resolve_backend() == "snowflake"
    assert be.resolve_backend("duckdb") == "duckdb"
    monkeypatch.setenv("DATA_BACKEND", "")
    assert be.resolve_backend() == "duckdb"


def test_duckdb_connect_uses_duckdb_path_read_only(monkeypatch, tmp_path):
    db = tmp_path / "w.duckdb"
    seed = duckdb.connect(str(db))
    seed.execute("create table t as select 1 as x")
    seed.close()
    monkeypatch.setenv("DUCKDB_PATH", str(db))
    with be.connect() as con:
        assert con.backend == "duckdb"
        assert con.read_sql("select x from t")["x"].tolist() == [1]
        assert con.read_sql("select x from t where x = ?", [1]).shape == (1, 1)
        with pytest.raises(duckdb.Error):
            con.execute("insert into t values (2)")


def test_duckdb_missing_file_is_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="DUCKDB_PATH"):
        be.connect(duckdb_path=tmp_path / "nope.duckdb")


def test_relative_duckdb_path_resolves_against_repo_root():
    assert be.resolve_duckdb_path("warehouse.duckdb") == be.ROOT / "warehouse.duckdb"
    assert be.resolve_duckdb_path() == be.ROOT / "warehouse.duckdb"


# -- snowflake connect: gate, defaults, no secrets --------------------------------------------------------------


@pytest.fixture
def fake_connector(monkeypatch):
    calls = {"connect": [], "key": [], "loaded": 0}

    class Connector:
        @staticmethod
        def connect(**kwargs):
            calls["connect"].append(kwargs)
            return FakeConn()

    def load_connector():
        calls["loaded"] += 1
        return Connector

    def load_key(path, passphrase):
        calls["key"].append((path, passphrase))
        return b"DER-BYTES"

    monkeypatch.setattr(be, "_load_snowflake_connector", load_connector)
    monkeypatch.setattr(be, "_load_private_key_der", load_key)
    return calls


def test_snowflake_missing_env_names_only(monkeypatch, fake_connector):
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
    with pytest.raises(be.MissingConfigError) as e:
        be.connect("snowflake", confirm=True)
    assert "SNOWFLAKE_USER" in str(e.value) and "SNOWFLAKE_PRIVATE_KEY_PATH" in str(e.value)
    assert fake_connector["loaded"] == 0
    with pytest.raises(be.MissingConfigError, match="SNOWFLAKE_ACCOUNT"):
        monkeypatch.delenv("SNOWFLAKE_ACCOUNT")
        be.connect("snowflake", confirm=True)


def test_snowflake_requires_confirmation_before_touching_key_or_connector(sf_env, fake_connector, capsys):
    with pytest.raises(be.ConfirmationRequired):
        be.connect("snowflake")
    assert fake_connector["loaded"] == 0 and fake_connector["key"] == [] and fake_connector["connect"] == []
    out = capsys.readouterr()
    text = out.out + out.err
    assert "account=acct-xy12345" in text and "database=RETAIL_OLIST" in text
    assert "role=RETAIL_TRANSFORMER" in text and "warehouse=RETAIL_WH" in text
    assert PASSPHRASE not in text and "someone" not in text and "key.p8" not in text


def test_snowflake_connect_with_confirm_uses_defaults_and_qmark(sf_env, fake_connector, capsys):
    db = be.connect("snowflake", confirm=True)
    assert db.backend == "snowflake"
    (kwargs,) = fake_connector["connect"]
    assert kwargs["account"] == "acct-xy12345" and kwargs["user"] == "someone"
    assert kwargs["role"] == "RETAIL_TRANSFORMER" and kwargs["warehouse"] == "RETAIL_WH"
    assert kwargs["database"] == "RETAIL_OLIST" and kwargs["paramstyle"] == "qmark"
    assert kwargs["private_key"] == b"DER-BYTES"
    assert fake_connector["key"] == [("/nonexistent/key.p8", PASSPHRASE)]
    printed = capsys.readouterr()
    assert PASSPHRASE not in printed.out + printed.err


def test_snowflake_confirm_env_and_overrides(sf_env, fake_connector, monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "snowflake")
    monkeypatch.setenv("RETAIL_SF_CONFIRM", "1")
    monkeypatch.setenv("RETAIL_SF_ROLE", "RETAIL_REPORTER")
    monkeypatch.setenv("RETAIL_SF_WAREHOUSE", "OTHER_WH")
    monkeypatch.setenv("RETAIL_SF_DATABASE", "OTHER_DB")
    monkeypatch.delenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    db = be.connect()
    (kwargs,) = fake_connector["connect"]
    assert (kwargs["role"], kwargs["warehouse"], kwargs["database"]) == ("RETAIL_REPORTER", "OTHER_WH", "OTHER_DB")
    assert fake_connector["key"][0][1] is None  # passphrase optional
    assert db.target.database == "OTHER_DB"


@pytest.mark.parametrize("value", ["0", "true", ""])
def test_only_confirm_one_counts(sf_env, fake_connector, monkeypatch, value):
    monkeypatch.setenv("RETAIL_SF_CONFIRM", value)
    with pytest.raises(be.ConfirmationRequired):
        be.connect("snowflake")


def test_private_key_loader_round_trip(tmp_path):
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.BestAvailableEncryption(b"pw"))
    path = tmp_path / "k.p8"
    path.write_bytes(pem)
    der = be._load_private_key_der(str(path), "pw")
    assert isinstance(der, bytes) and der[:1] == b"\x30"


# -- read_sql on the snowflake wrapper ---------------------------------------------------------------------------


@pytest.mark.parametrize("pandas_fetch", [True, False])
def test_snowflake_read_sql_normalises_and_binds_params(pandas_fetch):
    raw = pd.DataFrame({"WEEK": [date(2017, 1, 2)], "ORDERS": [Decimal(3)], "REVENUE": [Decimal("10.50")]})
    db = sf_wrapper([("from t", raw)], pandas_fetch)
    out = db.read_sql("select * from t where a = ?", [7])
    assert list(out.columns) == ["week", "orders", "revenue"]
    assert out["revenue"].dtype == "float64" and out["revenue"].iloc[0] == 10.5
    assert str(out["week"].dtype) == "datetime64[ns]"
    assert db.raw.log == [("select * from t where a = ?", (7,))]


def test_snowflake_execute_and_close():
    db = sf_wrapper()
    db.execute("delete from x where run_id = ?", ["r"])
    assert db.raw.log == [("delete from x where run_id = ?", ("r",))]
    db.close()
    assert db.raw.closed


# -- normalisation -----------------------------------------------------------------------------------------------


def test_normalise_dtypes():
    df = pd.DataFrame({
        "ID": ["a", "b", None],
        "AMOUNT": [Decimal("1.50"), None, Decimal(2)],
        "CNT": pd.Series([1, None, 3], dtype=object),
        "FLAG": pd.Series([True, False, True], dtype=object),
        "FLAG_NULL": pd.Series([True, None, False], dtype=object),
        "TS": pd.Series([datetime(2018, 1, 1, 12), None, datetime(2018, 1, 2)], dtype=object),
        "D": pd.Series([date(2018, 1, 1), date(2018, 1, 8), None], dtype=object),
        "US": pd.to_datetime(["2018-01-01", "2018-01-02", "2018-01-03"]).astype("datetime64[us]"),
        "PLAIN_INT": [1, 2, 3],
    })
    out = normalise_frame(df)
    assert list(out.columns) == [c.lower() for c in df.columns]
    assert out["amount"].dtype == "float64" and out["amount"].isna().tolist() == [False, True, False]
    assert str(out["cnt"].dtype) == "Int64" and out["cnt"].isna().tolist() == [False, True, False]
    assert out["flag"].dtype == "bool"
    assert str(out["flag_null"].dtype) == "boolean"
    assert str(out["ts"].dtype) == "datetime64[ns]" and out["ts"].isna().tolist() == [False, True, False]
    assert str(out["d"].dtype) == "datetime64[ns]"
    assert str(out["us"].dtype) == "datetime64[ns]"
    assert out["plain_int"].dtype == "int64"
    assert df.columns[0] == "ID"  # input not mutated


def test_conform_integral_floats_to_ints_and_numbers_to_float():
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": [1.0, 2.0, 3.0], "c": [1, 2, 3], "d": ["2018-01-01"] * 3, "x": [1, 2, 3]})
    out = conform_frame(df, {"b": "int", "a": "int", "c": "float", "d": "datetime"})
    assert list(out.columns) == ["b", "a", "c", "d", "x"]
    assert str(out["a"].dtype) == "Int64" and out["b"].dtype == "int64"
    assert out["c"].dtype == "float64" and str(out["d"].dtype).startswith("datetime64")
    non_integral = conform_frame(pd.DataFrame({"a": [1.5, 2.0]}), {"a": "int"})
    assert non_integral["a"].dtype == "float64"  # left for validate_frame to flag


# -- validate_frame ----------------------------------------------------------------------------------------------


def test_validate_frame_accepts_matching_frame_and_other_units():
    df = pd.DataFrame({"week": pd.to_datetime(["2017-01-02"]).astype("datetime64[us]"), "orders": [1], "revenue": [1]})
    assert validate_frame(df, WEEKLY_SERIES_SCHEMA) is df  # int is a valid float; any datetime unit


def test_validate_frame_fails_on_missing_column():
    df = pd.DataFrame({"week": pd.to_datetime(["2017-01-02"]), "orders": [1]})
    with pytest.raises(SchemaError, match="missing column 'revenue'"):
        validate_frame(df, WEEKLY_SERIES_SCHEMA, name="weekly_series")


@pytest.mark.parametrize("bad", [
    {"orders": [1.5]},                 # float where int expected
    {"orders": ["1"]},                 # text where int expected
    {"revenue": ["x"]},                # text where float expected
    {"week": ["2017-01-02"]},          # text where datetime expected
    {"revenue": [True]},               # bool is not a number here
])
def test_validate_frame_fails_on_wrong_dtype(bad):
    good = {"week": pd.to_datetime(["2017-01-02"]), "orders": [1], "revenue": [1.0]}
    with pytest.raises(SchemaError, match="expected kind"):
        validate_frame(pd.DataFrame({**good, **bad}), WEEKLY_SERIES_SCHEMA)


def test_validate_frame_extra_columns_policy():
    df = pd.DataFrame({"week": pd.to_datetime(["2017-01-02"]), "orders": [1], "revenue": [1.0], "extra": [1]})
    validate_frame(df, WEEKLY_SERIES_SCHEMA)
    with pytest.raises(SchemaError, match="unexpected column 'extra'"):
        validate_frame(df, WEEKLY_SERIES_SCHEMA, allow_extra=False)


# -- schemas match the DuckDB output; DuckDB path unchanged ------------------------------------------------------


def _populate(mini):
    t0 = datetime(2018, 1, 1, 10)
    for i in range(12):
        purchase = t0 + timedelta(days=9 * i)
        delivered = purchase + timedelta(days=10 + (i % 4) * 4)
        mini.add_order(purchase, delivered)
    mini.add_order(t0 + timedelta(days=3), None, status="canceled")
    mini.add_order(t0 + timedelta(days=40), t0 + timedelta(days=50), anomaly=True)
    return mini


@pytest.fixture
def populated(mini):
    return _populate(mini)


def test_schema_columns_match_the_duckdb_sql_output(populated):
    con = populated.con
    assert list(populated.features().reset_index().columns) == list(LATE_DELIVERY_FEATURES_SCHEMA)
    assert list(con.execute(datasets._WEEKLY_SERIES_DUCKDB).df().columns) == list(WEEKLY_SERIES_SCHEMA)
    assert list(con.execute(datasets._UNLABELLED_SHARE_DUCKDB).df().columns) == list(UNLABELLED_SHARE_SCHEMA)
    # and the frames from the DuckDB path validate against those schemas
    wrapped = be.wrap_duckdb(con)
    datasets.weekly_series(wrapped)
    datasets.late_delivery_features(wrapped)
    datasets.unlabelled_share(wrapped)


def test_duckdb_sql_text_matches_the_ml_modules():
    """The data_access copy of the SQL is the existing SQL: compare against the source of src/ml."""
    import inspect

    assert datasets._WEEKLY_SERIES_DUCKDB.strip() in inspect.getsource(fb.weekly_series)
    assert datasets._UNLABELLED_SHARE_DUCKDB.strip() in inspect.getsource(ldb.unlabelled_share)
    assert datasets.FEATURES_SQL == ldb.FEATURES_SQL


def test_weekly_series_duckdb_raw_and_wrapped_are_identical(populated):
    raw = fb.weekly_series(populated.con)
    wrapped = fb.weekly_series(be.wrap_duckdb(populated.con))
    assert_frame_equal(raw, wrapped)
    assert raw.index.name == "week" and raw.index.is_monotonic_increasing and len(raw) > 3


def test_load_duckdb_raw_and_wrapped_are_identical(populated):
    raw = ldb.load(populated.con)
    wrapped = ldb.load(be.wrap_duckdb(populated.con))
    assert_frame_equal(raw, wrapped)
    assert "month" in raw.columns and len(raw) == 12  # the canceled and the timestamp-anomalous orders are not in the population


def test_unlabelled_share_duckdb_raw_and_wrapped_are_identical(populated):
    raw = ldb.unlabelled_share(populated.con)
    assert raw == ldb.unlabelled_share(be.wrap_duckdb(populated.con))
    assert raw and all(isinstance(k, str) for k in raw)


def test_dataset_accepts_a_raw_duckdb_connection(populated):
    assert_frame_equal(datasets.weekly_series(populated.con), datasets.weekly_series(be.wrap_duckdb(populated.con)))
    with pytest.raises(KeyError, match="nope"):
        datasets.load_dataset("nope", populated.con)


# -- snowflake path of the datasets (fake cursor) ----------------------------------------------------------------


def test_snowflake_weekly_series_through_the_ml_function(populated):
    expected = fb.weekly_series(populated.con)
    raw = expected.reset_index()
    raw["week"] = raw["week"].dt.date
    raw["orders"] = raw["orders"].map(Decimal)
    raw["revenue"] = raw["revenue"].map(lambda v: Decimal(str(round(v, 2))))
    raw.columns = [c.upper() for c in raw.columns]
    db = sf_wrapper([("mart_weekly_orders_revenue", raw)])
    out = fb.weekly_series(db)
    assert_frame_equal(out, expected, check_dtype=False, check_index_type=False)
    (sql,) = db.raw.sql
    assert "MARTS.mart_weekly_orders_revenue" in sql and sql.rstrip().endswith("order by week")
    assert str(out.index.dtype).startswith("datetime64")


def test_snowflake_late_features_match_duckdb_after_load(populated):
    duck = populated.con.execute(datasets.FEATURES_SQL.read_text(encoding="utf-8")).df()
    sf = duck.copy()
    # what Snowflake NUMBER columns look like after normalisation: integral floats where DuckDB has ints
    for col in ("purchase_dow", "purchase_hour", "item_count", "n_sellers", "max_volume_cm3", "same_state"):
        sf[col] = sf[col].astype("float64")
    sf.columns = [c.upper() for c in sf.columns]
    db = sf_wrapper([("mart_late_delivery_features", sf)])
    out = ldb.load(db)
    (sql,) = db.raw.sql
    assert "MARTS.mart_late_delivery_features" in sql and "order by purchase_ts, order_id" in sql
    assert sql.startswith("select order_id, purchase_ts, ")
    assert_frame_equal(out, ldb.load(populated.con), check_dtype=False)


def test_snowflake_unlabelled_share_matches_duckdb(populated):
    expected = ldb.unlabelled_share(populated.con)
    rows = populated.con.execute(datasets._UNLABELLED_SHARE_DUCKDB).df()
    rows["n"] = rows["n"].map(Decimal)
    rows["labelled"] = rows["labelled"].map(Decimal)
    rows.columns = [c.upper() for c in rows.columns]
    db = sf_wrapper([("fact_orders", rows)])
    assert ldb.unlabelled_share(db) == expected
    assert "MARTS.fact_orders" in db.raw.sql[0] and "to_char(" in db.raw.sql[0]


def test_snowflake_dataset_with_missing_column_fails_validation():
    raw = pd.DataFrame({"WEEK": [date(2017, 1, 2)], "ORDERS": [3]})  # no REVENUE
    db = sf_wrapper([("mart_weekly_orders_revenue", raw)])
    with pytest.raises(SchemaError, match="revenue"):
        datasets.weekly_series(db)


def test_marts_schema_override_is_validated():
    db = sf_wrapper([("x", pd.DataFrame())])
    with pytest.raises(ValueError, match="invalid schema name"):
        datasets.weekly_series(db, marts_schema="MARTS; drop table x")


# -- write-back ----------------------------------------------------------------------------------------------------

FORBIDDEN = re.compile(r"\b(DROP|REPLACE|TRUNCATE|OVERWRITE)\b", re.IGNORECASE)


@pytest.fixture
def fake_write_pandas(monkeypatch):
    calls = []

    def write_pandas(conn, df, table_name, **kwargs):
        calls.append({"conn": conn, "df": df.copy(), "table": table_name, "kwargs": kwargs})
        return True, 1, len(df), []

    monkeypatch.setattr(writeback, "_write_pandas", lambda: write_pandas)
    return calls


def backtest_frame():
    return pd.DataFrame({
        "target": ["orders", "orders"], "horizon": [1, 1], "method": ["naive_last_week", "actual"],
        "target_week": pd.to_datetime(["2017-07-03", "2017-07-10"]), "forecast": [730.0, 841.0],
        "actual": [841.0, 959.0], "abs_error": [111.0, 118.0],
    })


def scores_frame():
    return pd.DataFrame({
        "order_id": ["o1", "o2"], "month": ["2018-03", "2018-03"], "purchase_date_key": [20180301, 20180302],
        "risk_score": [0.1, 0.2], "risk_percentile": [0.5, 1.0], "flagged_top10": [False, True], "is_late": [0, 1],
        "customer_state": ["RJ", "SP"], "seller_state": ["SP", "SP"], "category": ["toys", "unknown"],
        "promised_days": [15.0, 20.5],
    })


def test_writeback_is_off_by_default(fake_write_pandas):
    db = sf_wrapper()
    assert writeback.write_forecast_backtest(db, backtest_frame(), "run1") == 0
    assert db.raw.log == [] and fake_write_pandas == []
    assert writeback.writeback_enabled() is False


def test_writeback_env_opt_in_and_explicit_flag_wins(fake_write_pandas, monkeypatch):
    monkeypatch.setenv("FORECAST_WRITEBACK", "1")
    assert writeback.writeback_enabled() is True
    db = sf_wrapper()
    assert writeback.write_forecast_backtest(db, backtest_frame(), "run1", enabled=False) == 0
    assert db.raw.log == []
    assert writeback.write_forecast_backtest(db, backtest_frame(), "run1") == 2
    monkeypatch.setenv("FORECAST_WRITEBACK", "true")
    assert writeback.writeback_enabled() is False


def test_writeback_requires_a_snowflake_connection(fake_write_pandas):
    with pytest.raises(be.DataAccessError, match="Snowflake"):
        writeback.write_forecast_backtest(be.wrap_duckdb(duckdb.connect(":memory:")), backtest_frame(), "r", enabled=True)
    assert fake_write_pandas == []


@pytest.mark.parametrize("fn,frame", [
    (writeback.write_forecast_backtest, backtest_frame),
    (writeback.write_late_delivery_scores, scores_frame),
])
def test_writeback_statements_never_drop_or_replace(fake_write_pandas, fn, frame):
    db = sf_wrapper()
    n = fn(db, frame(), "run-42", enabled=True)
    assert n == 2
    statements = db.raw.sql
    assert len(statements) == 2
    assert statements[0].startswith("CREATE TABLE IF NOT EXISTS RETAIL_OLIST.ML.")
    assert re.fullmatch(r"DELETE FROM RETAIL_OLIST\.ML\.[A-Z_]+ WHERE run_id = \?", statements[1])
    assert db.raw.log[1][1] == ("run-42",)  # bound, not interpolated
    assert not any(FORBIDDEN.search(s) for s in statements)
    (call,) = fake_write_pandas
    kw = call["kwargs"]
    assert kw["auto_create_table"] is False and kw["overwrite"] is False and kw["quote_identifiers"] is False
    assert kw["schema"] == "ML" and kw["database"] == "RETAIL_OLIST"
    assert call["table"] in ("FORECAST_BACKTEST", "LATE_DELIVERY_SCORES")
    assert call["df"].columns[0] == "RUN_ID" and set(call["df"]["RUN_ID"]) == {"run-42"}
    assert all(c == c.upper() for c in call["df"].columns)


def test_writeback_columns_match_export_schemas(fake_write_pandas):
    """Table columns are the Power BI export columns (model_spec FIXED_SCHEMAS) plus run_id."""
    from model_spec import FIXED_SCHEMAS

    for table, spec in (("FORECAST_BACKTEST", "forecast_backtest"), ("LATE_DELIVERY_SCORES", "late_delivery_scores"),
                        ("FLAG_SHARE", "flag_share")):
        assert [c for c, _ in writeback.TABLE_COLUMNS[table]] == ["run_id"] + [c for c, _ in FIXED_SCHEMAS[spec]]


def test_writeback_target_week_is_written_as_date(fake_write_pandas):
    writeback.write_forecast_backtest(sf_wrapper(), backtest_frame(), "r", enabled=True)
    assert fake_write_pandas[0]["df"]["TARGET_WEEK"].tolist() == [date(2017, 7, 3), date(2017, 7, 10)]


def test_writeback_flag_share_defaults(fake_write_pandas):
    db = sf_wrapper()
    assert writeback.write_flag_share(db, "r", enabled=True) == 6
    assert fake_write_pandas[0]["df"]["FLAG_PCT"].tolist() == [5, 10, 15, 20, 25, 30]
    assert "FLAG_SHARE" in db.raw.sql[0]


def test_writeback_validates_before_touching_snowflake(fake_write_pandas):
    db = sf_wrapper()
    with pytest.raises(SchemaError, match="abs_error"):
        writeback.write_forecast_backtest(db, backtest_frame().drop(columns="abs_error"), "r", enabled=True)
    with pytest.raises(ValueError, match="run_id"):
        writeback.write_forecast_backtest(db, backtest_frame(), " ", enabled=True)
    assert db.raw.log == [] and fake_write_pandas == []


def test_writeback_failed_load_raises(monkeypatch):
    monkeypatch.setattr(writeback, "_write_pandas", lambda: (lambda *a, **k: (False, 0, 0, [])))
    with pytest.raises(be.DataAccessError, match="write_pandas"):
        writeback.write_forecast_backtest(sf_wrapper(), backtest_frame(), "r", enabled=True)


def test_new_run_id_is_unique_and_non_empty():
    assert writeback.new_run_id() != writeback.new_run_id()


def test_create_table_sql_is_idempotent_ddl():
    sql = writeback.create_table_sql(sf_wrapper(), "FLAG_SHARE")
    assert sql.startswith("CREATE TABLE IF NOT EXISTS RETAIL_OLIST.ML.FLAG_SHARE") and not FORBIDDEN.search(sql)


# -- real warehouse (skipped when warehouse.duckdb has not been built) ---------------------------------------------


def check_wrapped_equals_raw(path):
    """DuckDB path through the wrapper == the plain connection. threads=1: the history columns of the feature SQL
    (seller_prior_late_rate, category_prior_n/_late) are not reproducible between multi-threaded runs of the SQL
    itself, which is unrelated to the wrapper (observed on the real warehouse: raw-vs-raw differs too)."""
    con = duckdb.connect(str(path), read_only=True)
    con.execute("set threads=1")
    wrapped = be.wrap_duckdb(con)
    assert_frame_equal(fb.weekly_series(con), fb.weekly_series(wrapped))
    assert_frame_equal(ldb.load(con), ldb.load(wrapped))
    assert ldb.unlabelled_share(con) == ldb.unlabelled_share(wrapped)
    con.close()


@pytest.mark.warehouse
def test_real_warehouse_wrapped_equals_raw_and_validates(warehouse):
    from conftest import WAREHOUSE

    check_wrapped_equals_raw(WAREHOUSE)

# ------------------------------------------------------------------------------------ entry points: --backend / --yes


@pytest.mark.parametrize("module_name", ["forecast_baseline", "late_delivery_baseline"])
def test_entry_points_reject_unknown_backend_from_env(module_name, monkeypatch):
    import importlib
    mod = importlib.import_module(module_name)
    monkeypatch.setenv("DATA_BACKEND", "oracle")
    monkeypatch.setattr("sys.argv", [module_name])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 2


@pytest.mark.parametrize("module_name", ["forecast_baseline", "late_delivery_baseline"])
def test_entry_points_snowflake_backend_needs_config_and_confirmation(module_name, monkeypatch, tmp_path):
    """--backend snowflake must stop before any connection: no env -> MissingConfigError, env but no --yes -> ConfirmationRequired."""
    import importlib
    from data_access import backend as be
    mod = importlib.import_module(module_name)
    for name in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH", "RETAIL_SF_CONFIRM"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(be, "_load_snowflake_connector",
                        lambda: pytest.fail("the Snowflake connector must not be imported without confirmation"))
    argv = [module_name, "--backend", "snowflake", "--out", str(tmp_path / "out.json")]
    monkeypatch.setattr("sys.argv", argv)
    with pytest.raises(be.MissingConfigError):
        mod.main()
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct-placeholder")
    monkeypatch.setenv("SNOWFLAKE_USER", "user-placeholder")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PATH", str(tmp_path / "no_such_key.p8"))
    with pytest.raises(be.ConfirmationRequired):
        mod.main()
    assert not (tmp_path / "out.json").exists()


def test_yes_flag_is_passed_to_connect_as_confirmation(monkeypatch):
    """--backend snowflake --yes reaches data_access.connect as confirm=True (and nothing else connects first)."""
    import forecast_baseline as fb
    seen = {}

    def fake_connect(backend, confirm=False):
        seen["backend"], seen["confirm"] = backend, confirm
        raise RuntimeError("stop after connect")

    import data_access
    monkeypatch.setattr(data_access, "connect", fake_connect)
    monkeypatch.setattr("sys.argv", ["forecast_baseline", "--backend", "snowflake", "--yes"])
    with pytest.raises(RuntimeError, match="stop after connect"):
        fb.main()
    assert seen == {"backend": "snowflake", "confirm": True}
