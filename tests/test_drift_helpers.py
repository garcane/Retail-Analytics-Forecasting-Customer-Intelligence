import numpy as np
import pandas as pd
import pytest

import drift_analysis as da

T = pd.Timestamp


def frame():
    # three orders resolved on days 10, 11, 12 (the second one late), and probes bought on days 5, 11 and 20
    return pd.DataFrame({
        "purchase_ts": [T("2018-01-01"), T("2018-01-02"), T("2018-01-03"), T("2018-01-06"), T("2018-01-12"), T("2018-01-21")],
        "delivered_customer_ts": [T("2018-01-11"), T("2018-01-12"), T("2018-01-13"), T("2018-02-01"), T("2018-02-01"), T("2018-02-01")],
        "is_late": [0, 1, 0, 0, 0, 0],
    })


def test_system_counts_use_only_orders_delivered_strictly_before_purchase():
    out = da.with_system_counts(frame())
    # purchases on days 1-3 and 6 see nothing; day 12 sees the deliveries of days 11 and 12; day 21 sees all three
    assert out["sys_n"].tolist() == [0, 0, 0, 0, 1, 3]
    assert out["sys_late"].tolist() == [0, 0, 0, 0, 0, 1]


def test_system_counts_do_not_depend_on_row_order():
    df = frame()
    shuffled = df.sample(frac=1, random_state=0).reset_index(drop=True)
    a = da.with_system_counts(df).sort_values("purchase_ts").reset_index(drop=True)
    b = da.with_system_counts(shuffled).sort_values("purchase_ts").reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_relative_rates_are_zero_when_route_matches_the_system():
    df = pd.DataFrame({
        "route_prior_n": [1000.0], "route_prior_late": [80.0], "category_prior_n": [1000.0], "category_prior_late": [80.0],
        "recent_n_28d": [0.0], "recent_late_28d": [0.0], "sys_n": [100000.0], "sys_late": [8000.0],
    })
    out = da.add_relative_rates(df, prior=0.08)
    assert out.loc[0, "route_rel"] == pytest.approx(0.0, abs=1e-9)
    assert out.loc[0, "category_rel"] == pytest.approx(0.0, abs=1e-9)


def test_relative_rates_are_positive_for_a_late_route():
    df = pd.DataFrame({
        "route_prior_n": [1000.0], "route_prior_late": [200.0], "category_prior_n": [1000.0], "category_prior_late": [80.0],
        "recent_n_28d": [0.0], "recent_late_28d": [0.0], "sys_n": [100000.0], "sys_late": [8000.0],
    })
    out = da.add_relative_rates(df, prior=0.08)
    assert out.loc[0, "route_rel"] > 0.1 and abs(out.loc[0, "category_rel"]) < 1e-6
    assert np.isfinite(out["route_rel"]).all()
