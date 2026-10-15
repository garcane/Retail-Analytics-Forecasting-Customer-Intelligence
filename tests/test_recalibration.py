import numpy as np
import pandas as pd
import pytest

import recalibration as rc

T = pd.Timestamp
MONTH = pd.Period("2018-04", freq="M")  # starts 2018-04-01; gap 28 days -> calibration purchases end 2018-03-04


def orders():
    """Orders purchased every 5 days from 2017-01-01 to 2018-05-31, each delivered 12 days after purchase."""
    purchase = pd.date_range("2017-01-01", "2018-05-31", freq="5D")
    return pd.DataFrame({
        "purchase_ts": purchase,
        "delivered_customer_ts": purchase + pd.Timedelta(days=12),
        "is_late": np.arange(len(purchase)) % 7 == 0,
    }).assign(month=lambda d: d["purchase_ts"].dt.to_period("M"))


def test_split_uses_only_outcomes_known_before_the_test_month():
    base, calib = rc.calibration_split(orders(), MONTH, window_months=2)
    start = MONTH.start_time
    assert (calib["delivered_customer_ts"] < start).all()
    assert (calib["purchase_ts"] < start - pd.Timedelta(days=rc.GAP_DAYS)).all()
    assert len(calib) > 0 and len(base) > 0


def test_base_model_outcomes_are_known_before_the_calibration_window_starts():
    base, calib = rc.calibration_split(orders(), MONTH, window_months=2)
    assert base["delivered_customer_ts"].max() < calib["purchase_ts"].min()


def test_base_and_calibration_rows_do_not_overlap():
    base, calib = rc.calibration_split(orders(), MONTH, window_months=1)
    assert base.index.intersection(calib.index).empty


def test_wider_window_gives_more_calibration_rows():
    _, one = rc.calibration_split(orders(), MONTH, window_months=1)
    _, two = rc.calibration_split(orders(), MONTH, window_months=2)
    assert len(two) > len(one)


def test_shift_calibrator_matches_the_observed_rate():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.02, 0.4, 5000)
    y = (rng.random(5000) < 0.05).astype(int)  # model over-predicts: mean p is about 0.21
    calibrated = rc.make_calibrator("shift", p, y)(p)
    assert calibrated.mean() == pytest.approx(y.mean(), abs=1e-6)
    assert np.all(np.diff(calibrated[np.argsort(p)]) >= -1e-12)  # monotone: ranking is untouched


@pytest.mark.parametrize("kind", ["shift", "platt", "isotonic"])
def test_calibrators_return_probabilities(kind):
    rng = np.random.default_rng(1)
    p = rng.uniform(0.01, 0.6, 3000)
    y = (rng.random(3000) < p / 2).astype(int)
    out = rc.make_calibrator(kind, p, y)(p)
    assert out.shape == p.shape and (out >= 0).all() and (out <= 1).all()


def test_platt_reduces_overconfidence():
    rng = np.random.default_rng(2)
    true = rng.uniform(0.02, 0.2, 20000)
    y = (rng.random(20000) < true).astype(int)
    p = np.clip(true * 2, 0, 1)  # twice as confident as the truth
    before = rc.score(y, p)["brier"]
    after = rc.score(y, rc.make_calibrator("platt", p, y)(p))["brier"]
    assert after < before


def test_unknown_calibrator_is_rejected():
    with pytest.raises(ValueError):
        rc.make_calibrator("magic", np.array([0.1, 0.2]), np.array([0, 1]))


def test_ece_is_zero_for_a_perfectly_calibrated_split():
    y = np.array([0, 0, 0, 1] * 5)
    p = np.full(20, 0.25)
    assert rc.expected_calibration_error(y, p) == pytest.approx(0.0, abs=1e-9)
