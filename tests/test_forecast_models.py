import numpy as np
import pandas as pd
import pytest

import explain_late_delivery as eld
import forecast_baseline as fb
import forecast_models as fm
import late_delivery_baseline as ldb


def series(values):
    return pd.Series(values, index=pd.date_range("2017-01-02", periods=len(values), freq="W-MON"), dtype=float)


def test_no_model_sees_weeks_after_its_origin():
    rng = np.random.default_rng(3)
    base = series(rng.integers(100, 500, 55))
    changed = base.copy()
    changed.iloc[40:] += 5_000
    for h in fb.HORIZONS:
        a, b = fb.backtest(base, h, fm.MODELS), fb.backtest(changed, h, fm.MODELS)
        safe = a.index[a.index < base.index[40 + h]]
        assert len(safe) > 0
        pd.testing.assert_frame_equal(a.loc[safe].drop(columns="actual"), b.loc[safe].drop(columns="actual"))


def test_constant_series_is_forecast_as_constant_by_every_model():
    flat = np.full(40, 250.0)
    for name, f in fm.MODELS.items():
        assert f(flat, 4) == pytest.approx(250.0, abs=1e-3), name


def test_damped_trend_continues_a_rising_series_but_less_than_a_straight_line():
    rising = np.arange(1, 41) * 10.0
    forecast = fm.damped_trend(rising, 4)
    assert rising[-1] < forecast < rising[-1] + 4 * 10.0 + 1e-6


def test_exponential_smoothing_follows_the_latest_level_after_a_step():
    step = np.concatenate([np.full(30, 100.0), np.full(10, 300.0)])
    assert fm.simple_exponential_smoothing(step) > 250


def test_ar1_trend_extends_an_exact_linear_series():
    line = 5.0 + 2.0 * np.arange(40)
    assert fm.ar1_with_trend(26)(line, 2) == pytest.approx(5.0 + 2.0 * 41, rel=1e-6)


def test_combination_is_the_mean_of_its_parts():
    history = np.arange(1, 31, dtype=float)
    expected = (history[-1] + history[-8:].mean()) / 2
    assert fm.combination(history, 1) == pytest.approx(expected)


def test_forecasts_are_never_negative():
    falling = np.maximum(200 - 10.0 * np.arange(40), 0.0)
    for name, f in fm.MODELS.items():
        assert f(falling, 4) >= 0, name


def test_explainability_groups_cover_every_v1_feature_exactly_once():
    flat = [c for cols in eld.GROUPS.values() for c in cols]
    assert sorted(flat) == sorted(ldb.NUMERIC_V1 + ldb.CATEGORICAL)
    assert len(flat) == len(set(flat))
