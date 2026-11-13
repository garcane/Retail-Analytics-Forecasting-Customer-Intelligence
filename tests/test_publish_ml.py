"""src/ml/publish_ml.py: the gate, the dry-run default and one run_id across the three ML tables. No Snowflake."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("src", "src/ml", "src/powerbi"):
    sys.path.insert(0, str(ROOT / sub))

import publish_ml  # noqa: E402
from data_access.backend import ConfirmationRequired  # noqa: E402


class FakeDB:
    backend = "snowflake"

    def __init__(self):
        self.read_back = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def frames():
    scores = pd.DataFrame({
        "order_id": ["o1", "o2"], "month": ["2018-03", "2018-03"], "purchase_date_key": [20180301, 20180302],
        "risk_score": [0.1, 0.9], "risk_percentile": [0.5, 1.0], "flagged_top10": [False, True], "is_late": [0, 1],
        "customer_state": ["RJ", "SP"], "seller_state": ["SP", "SP"], "category": ["toys", "unknown"],
        "promised_days": [15.0, 20.5],
    })
    backtest = pd.DataFrame({
        "target": ["orders"], "horizon": [1], "method": ["naive_last_week"], "target_week": [pd.Timestamp("2017-07-03").date()],
        "forecast": [730.0], "actual": [841.0], "abs_error": [111.0],
    })
    return scores, backtest


@pytest.fixture
def patched(monkeypatch):
    scores, backtest = frames()
    db = FakeDB()
    writes = []
    monkeypatch.setattr(publish_ml, "connect", lambda backend, confirm: db)
    monkeypatch.setattr(publish_ml.export_scores, "build_from", lambda con: scores)
    monkeypatch.setattr(publish_ml.export_data, "forecast_backtest", lambda con: backtest)

    def write_table(conn, table, df, run_id, *, enabled=None, schema="ML"):
        writes.append((table, len(df), run_id, enabled))
        return len(df)

    monkeypatch.setattr(publish_ml.writeback, "write_table", write_table)
    monkeypatch.setattr(publish_ml, "written_rows", lambda conn, run_id: {t: n for t, n, r, _ in writes if r == run_id})
    return writes


def test_refuses_without_confirmation(monkeypatch, capsys):
    def connect(backend, confirm):
        raise ConfirmationRequired("refusing")

    monkeypatch.setattr(publish_ml, "connect", connect)
    assert publish_ml.main([]) == 1
    assert "refusing" in capsys.readouterr().err


def test_dry_run_is_the_default_and_writes_nothing(patched, capsys):
    assert publish_ml.main(["--yes"]) == 0
    assert patched == []
    assert "dry run" in capsys.readouterr().out


def test_write_uses_one_run_id_for_all_three_tables(patched):
    assert publish_ml.main(["--yes", "--write"]) == 0
    assert [t for t, *_ in patched] == ["LATE_DELIVERY_SCORES", "FORECAST_BACKTEST", "FLAG_SHARE"]
    assert len({r for _, _, r, _ in patched}) == 1
    assert all(enabled is True for *_, enabled in patched)
    assert dict((t, n) for t, n, *_ in patched)["FLAG_SHARE"] == 6


def test_explicit_run_id_is_used(patched):
    assert publish_ml.main(["--yes", "--write", "--run-id", "20261113T000000Z-abcdef01"]) == 0
    assert {r for _, _, r, _ in patched} == {"20261113T000000Z-abcdef01"}


@pytest.mark.parametrize("bad", ["test1", "rerun", "manual-fix", "20261113T000000Z-abc", "2026-11-13"])
def test_hand_picked_run_ids_are_refused_before_connecting(bad, monkeypatch, capsys):
    """Consumers take the text-greatest run_id as the latest; 'test1' would outrank every timestamped run for good."""
    monkeypatch.setattr(publish_ml, "connect", lambda *a, **k: pytest.fail("connected despite a bad --run-id"))
    with pytest.raises(SystemExit) as exc:
        publish_ml.main(["--yes", "--write", "--run-id", bad])
    assert exc.value.code == 2 and "--run-id must be" in capsys.readouterr().err


def test_generated_run_ids_have_the_accepted_form_and_sort_by_time():
    a = publish_ml.writeback.new_run_id()
    assert publish_ml.writeback.GENERATED_RUN_ID.match(a)
    assert "20261113T122357Z-ffffffff" < "20261113T122358Z-00000000"


def test_read_back_mismatch_fails(patched, monkeypatch):
    monkeypatch.setattr(publish_ml, "written_rows", lambda conn, run_id: {"LATE_DELIVERY_SCORES": 1})
    with pytest.raises(publish_ml.DataAccessError, match="read-back mismatch"):
        publish_ml.main(["--yes", "--write"])


def test_compute_rejects_a_frame_with_a_missing_column(monkeypatch):
    scores, backtest = frames()
    monkeypatch.setattr(publish_ml.export_scores, "build_from", lambda con: scores.drop(columns="category"))
    monkeypatch.setattr(publish_ml.export_data, "forecast_backtest", lambda con: backtest)
    with pytest.raises(Exception, match="category"):
        publish_ml.compute(FakeDB())
