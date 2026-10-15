"""The forecast baselines must only use weeks up to the forecast origin."""

import numpy as np
import pandas as pd
import pytest

import forecast_baseline as fb


def series(values):
    return pd.Series(values, index=pd.date_range("2017-01-02", periods=len(values), freq="W-MON"), dtype=float)


def test_changing_future_weeks_does_not_change_earlier_forecasts():
    rng = np.random.default_rng(0)
    base = series(rng.integers(100, 500, 60))
    changed = base.copy()
    changed.iloc[45:] += 10_000  # a huge shock from week 45 onward
    for h in fb.HORIZONS:
        a, b = fb.backtest(base, h), fb.backtest(changed, h)
        # the forecast for target week w is made at week w-h, so it can only differ when w-h >= 45
        safe = a.index[a.index < base.index[45 + h]]
        assert len(safe) > 0
        pd.testing.assert_frame_equal(a.loc[safe].drop(columns="actual"), b.loc[safe].drop(columns="actual"))


def test_naive_and_moving_average_values():
    s = series(range(1, 41))
    first = fb.backtest(s, 1).iloc[0]  # origin = week index 25 (value 26), target = value 27
    assert first["actual"] == 27
    assert first["naive_last_week"] == 26
    assert first["moving_average_4"] == pytest.approx(np.mean([23, 24, 25, 26]))
    assert first["moving_average_8"] == pytest.approx(np.mean(range(19, 27)))
    assert first["linear_trend_12"] == pytest.approx(27)  # a perfect line is extended exactly


def test_horizon_shifts_the_target():
    s = series(range(1, 41))
    assert fb.backtest(s, 4).iloc[0]["actual"] == 30


def test_score_is_below_one_for_a_better_model_than_naive():
    s = series(np.arange(1, 61) * 10.0)  # a clean trend: the line should beat last-value
    res = fb.score(fb.backtest(s, 4))
    assert res["linear_trend_12"]["mae_vs_naive"] < 1
    assert res["naive_last_week"]["mae_vs_naive"] == 1
