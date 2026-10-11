import numpy as np
import pandas as pd
import pytest

import late_delivery_baseline as ldb

HISTORY_COLUMNS = ["route_prior_n", "route_prior_late", "category_prior_n", "category_prior_late",
                   "recent_n_28d", "recent_late_28d"]


def test_smoothing_returns_prior_without_history_and_raw_rate_with_lots():
    df = pd.DataFrame({c: [0, 0] for c in HISTORY_COLUMNS})
    df["route_prior_n"], df["route_prior_late"] = [0, 1_000_000], [0, 500_000]
    out = ldb.add_smoothed_rates(df, prior=0.08)
    assert out.loc[0, "route_rate"] == pytest.approx(0.08)
    assert out.loc[1, "route_rate"] == pytest.approx(0.5, abs=1e-3)
    assert (out["category_rate"] == 0.08).all() and (out["recent_rate_28d"] == 0.08).all()


def test_smoothing_does_not_modify_the_input():
    df = pd.DataFrame({c: [1] for c in HISTORY_COLUMNS})
    ldb.add_smoothed_rates(df, 0.1)
    assert "route_rate" not in df.columns


def test_top_share_metrics():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    score = np.array([0.9, 0.1, 0.8, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.0])
    m = ldb.top_share_metrics(y, score, 0.2)  # flag two orders: scores 0.9 (late) and 0.8 (not late)
    assert m == {"precision_at_top": 0.5, "recall_at_top": 0.5}


def test_every_feature_set_is_a_superset_of_the_previous_one():
    assert set(ldb.NUMERIC_V1) < set(ldb.NUMERIC_V2) < set(ldb.NUMERIC_V3)


def test_calendar_month_is_not_a_feature():
    assert "purchase_month" not in ldb.NUMERIC_V3 + ldb.CATEGORICAL
