"""Leakage rules from docs/ml/LEAKAGE_ANALYSIS.md, checked on a tiny hand-built warehouse."""

from datetime import datetime, timedelta

import pytest

D = datetime(2018, 1, 1)


def day(n: float) -> datetime:
    return D + timedelta(days=n)


def test_history_counts_orders_delivered_before_purchase_not_purchased_before(mini):
    # six late orders bought on days 0-5 and delivered on days 10-15
    for i in range(6):
        mini.add_order(day(i), day(10 + i), late=True)
    early = mini.add_order(day(8), day(30), late=False)        # bought day 8: nothing delivered yet
    mid = mini.add_order(day(12.5), day(40), late=False)       # bought day 12.5: deliveries on days 10, 11, 12 known
    late_buyer = mini.add_order(day(20), day(50), late=False)  # all six resolved; `early` and `mid` still in transit
    f = mini.features()
    assert f.loc[early, "seller_prior_n"] == 0
    assert f.loc[early, "route_prior_n"] == 0 and f.loc[early, "category_prior_n"] == 0
    assert f.loc[mid, "route_prior_n"] == 3 and f.loc[mid, "route_prior_late"] == 3
    assert f.loc[late_buyer, "seller_prior_n"] == 6
    assert f.loc[late_buyer, "route_prior_n"] == 6 and f.loc[late_buyer, "category_prior_n"] == 6
    assert f.loc[late_buyer, "seller_prior_late_rate"] == 1.0


def test_an_order_never_sees_its_own_outcome(mini):
    only = mini.add_order(day(0), day(10), late=True)
    f = mini.features()
    assert f.loc[only, ["seller_prior_n", "route_prior_n", "category_prior_n", "recent_n_28d"]].tolist() == [0, 0, 0, 0]


def test_outcome_is_not_visible_at_the_instant_of_delivery(mini):
    mini.add_order(day(0), day(10), late=True)
    same_instant = mini.add_order(day(10), day(25), late=False)  # bought exactly when the first was delivered
    just_after = mini.add_order(day(10) + timedelta(seconds=1), day(26), late=False)
    f = mini.features()
    assert f.loc[same_instant, "route_prior_n"] == 0
    assert f.loc[just_after, "route_prior_n"] == 1


def test_seller_rate_needs_five_resolved_orders(mini):
    for i in range(4):
        mini.add_order(day(i), day(5 + i), late=True)
    four = mini.add_order(day(20), day(30), late=False)
    mini.add_order(day(21), day(22), late=True)  # a fifth order, resolved on day 22
    five = mini.add_order(day(23), day(31), late=False)
    f = mini.features()
    assert f.loc[four, "seller_prior_n"] == 4 and f.isna().loc[four, "seller_prior_late_rate"]
    assert f.loc[five, "seller_prior_n"] == 5 and f.loc[five, "seller_prior_late_rate"] == 1.0


def test_trailing_28_day_window_boundaries(mini):
    t = day(100)
    mini.add_order(day(0), t - timedelta(days=28) - timedelta(seconds=1), late=True)  # just outside the window
    mini.add_order(day(1), t - timedelta(days=28), late=True)                          # first instant inside
    mini.add_order(day(2), t - timedelta(seconds=1), late=False)                       # last instant inside
    mini.add_order(day(3), t, late=True)                                               # delivered at t: not yet known
    probe = mini.add_order(t, t + timedelta(days=20), late=False)
    f = mini.features()
    assert f.loc[probe, "recent_n_28d"] == 2
    assert f.loc[probe, "recent_late_28d"] == 1


def test_unlabelled_and_anomalous_orders_are_neither_rows_nor_history(mini):
    mini.add_order(day(0), None, late=None, status="shipped")
    mini.add_order(day(1), day(5), late=True, status="canceled")
    mini.add_order(day(2), day(6), late=True, anomaly=True)
    mini.add_order(day(3), None, late=None)  # "delivered" status but no delivery date
    probe = mini.add_order(day(30), day(40), late=False)
    f = mini.features()
    assert list(f.index) == [probe]
    assert f.loc[probe, "route_prior_n"] == 0 and f.loc[probe, "recent_n_28d"] == 0


def test_output_has_no_post_outcome_columns(mini):
    mini.add_order(day(0), day(10), late=False)
    columns = set(mini.features().reset_index().columns)
    forbidden = ("carrier", "approved", "delivery_days", "delivery_delay", "order_status", "review",
                 "shipping_limit", "anomaly", "estimated_delivery_ts")
    assert not [c for c in columns if any(word in c for word in forbidden)]
    # delivered_customer_ts is returned only so the training code can drop rows whose outcome was not yet known
    assert "delivered_customer_ts" in columns and "is_late" in columns


def test_one_row_per_order_with_multiple_items_and_sellers(mini):
    oid = mini.add_order(day(0), day(10), late=False)
    mini.con.execute("insert into fact_order_items values (?, 2, 1, 50, 5, 2, 1)", [oid])
    mini.con.execute("insert into dim_seller values (2, 'MG')")
    f = mini.features()
    assert f.index.is_unique and f.loc[oid, "n_sellers"] == 2


@pytest.mark.parametrize("late_flag", [True, False])
def test_label_is_passed_through_as_integer(mini, late_flag):
    oid = mini.add_order(day(0), day(10), late=late_flag)
    assert mini.features().loc[oid, "is_late"] == int(late_flag)
