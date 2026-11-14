"""src/data_access/snowpark.py with a fake Snowpark session (no Snowflake)."""

import importlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_access import datasets, is_data_access  # noqa: E402
from data_access.snowpark import SnowparkAccess  # noqa: E402


class FakeResult:
    def __init__(self, frame):
        self.frame = frame

    def to_pandas(self):
        return self.frame.copy()

    def collect(self):
        return []


class FakeSession:
    def __init__(self, frames=None):
        self.calls = []
        self.frames = frames or {}
        self.database = None
        self.connection = object()

    def use_database(self, name):
        self.database = name

    def get_current_account(self):
        return '"ACCT"'

    def get_current_database(self):
        return f'"{self.database}"' if self.database else None

    def get_current_role(self):
        return '"RETAIL_TRANSFORMER"'

    def get_current_warehouse(self):
        return '"RETAIL_WH"'

    def sql(self, query, params=None):
        self.calls.append((query, params))
        frame = next((f for pat, f in self.frames.items() if pat in query), pd.DataFrame({"N": [1]}))
        return FakeResult(frame)


def test_importing_the_module_does_not_import_snowflake():
    sys.modules.pop("snowflake.snowpark.context", None)
    importlib.reload(sys.modules["data_access.snowpark"])
    assert "snowflake.snowpark.context" not in sys.modules


def test_is_a_data_access_look_alike_with_a_clean_target():
    s = FakeSession()
    db = SnowparkAccess(s)
    assert is_data_access(db) and db.backend == "snowflake"
    assert s.database == "RETAIL_OLIST"
    assert (db.target.database, db.target.role, db.target.warehouse) == ("RETAIL_OLIST", "RETAIL_TRANSFORMER", "RETAIL_WH")
    assert db.raw is s.connection


def test_read_sql_binds_params_and_normalises_columns():
    s = FakeSession({"from x": pd.DataFrame({"ORDER_ID": ["a"], "N": [3]})})
    db = SnowparkAccess(s)
    df = db.read_sql("select * from x where run_id = ?", ["r1"])
    assert list(df.columns) == ["order_id", "n"]
    assert s.calls[-1] == ("select * from x where run_id = ?", ["r1"])
    db.read_sql("select 1")
    assert s.calls[-1] == ("select 1", None)


def test_execute_runs_and_close_keeps_the_session():
    s = FakeSession()
    with SnowparkAccess(s) as db:
        db.execute("select 1")
    assert s.calls[-1] == ("select 1", None)


def test_datasets_take_the_snowflake_branch_through_the_adapter():
    weekly = pd.DataFrame({"WEEK": pd.to_datetime(["2017-01-02", "2017-01-09"]), "ORDERS": [10, 12],
                           "REVENUE": [100.0, 120.5]})
    s = FakeSession({"mart_weekly_orders_revenue": weekly})
    out = datasets.weekly_series(SnowparkAccess(s))
    assert "MARTS.mart_weekly_orders_revenue" in s.calls[-1][0]
    assert list(out.columns)[:3] == ["week", "orders", "revenue"] and len(out) == 2
