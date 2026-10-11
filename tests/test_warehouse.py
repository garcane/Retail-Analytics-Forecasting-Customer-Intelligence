"""Checks against the real, built warehouse. Skipped when warehouse.duckdb has not been built."""

import pytest

import forecast_baseline as fb
from conftest import FEATURES_SQL, ROOT

pytestmark = pytest.mark.warehouse


def test_all_validation_checks_pass(warehouse):
    results = warehouse.execute((ROOT / "sql" / "validation" / "checks.sql").read_text(encoding="utf-8")).fetchall()
    failed = [r[0] for r in results if not r[3]]
    assert len(results) == 22 and not failed


@pytest.fixture(scope="module")
def features(warehouse):
    return warehouse.execute(FEATURES_SQL.read_text(encoding="utf-8")).df()


def test_feature_table_matches_the_documented_population(warehouse, features):
    expected = warehouse.execute(
        "select count(*), sum(is_late::int) from fact_orders "
        "where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly"
    ).fetchone()
    assert features["order_id"].is_unique
    assert (len(features), int(features["is_late"].sum())) == tuple(int(x) for x in expected)


def test_recent_28d_matches_a_direct_recount_on_real_data(warehouse, features):
    for _, r in features.sample(40, random_state=7).iterrows():
        n, late = warehouse.execute(
            """select count(*), count(*) filter (where is_late) from fact_orders
               where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
                 and delivered_customer_ts <  ? and delivered_customer_ts >= ? - interval 28 day""",
            [r["purchase_ts"], r["purchase_ts"]],
        ).fetchone()
        assert (n, late) == (r["recent_n_28d"], r["recent_late_28d"])


def test_seller_history_matches_a_direct_recount_on_real_data(warehouse, features):
    checked = 0
    for _, r in features[features["seller_prior_n"] >= 5].sample(60, random_state=3).iterrows():
        sellers = warehouse.execute("select distinct seller_key from fact_order_items where order_id = ?",
                                    [r["order_id"]]).fetchall()
        if len(sellers) != 1:
            continue  # the feature averages over sellers; the recount below is for single-seller orders
        n, rate = warehouse.execute(
            """select count(distinct o.order_id), avg(o.is_late::int) from fact_order_items oi
               join fact_orders o using (order_id)
               where oi.seller_key = ? and o.order_status = 'delivered' and o.is_late is not null
                 and o.delivered_customer_ts < ? and o.order_id <> ?""",
            [sellers[0][0], r["purchase_ts"], r["order_id"]],
        ).fetchone()
        assert n == r["seller_prior_n"] and rate == pytest.approx(r["seller_prior_late_rate"])
        checked += 1
    assert checked >= 20


def test_weekly_series_covers_the_documented_window(warehouse):
    weekly = fb.weekly_series(warehouse)
    main = weekly.loc[fb.FIRST_WEEK:fb.LAST_CLEAN_WEEK]
    assert len(main) == 85 and (main["orders"] > 0).all()
    assert weekly.loc[fb.SUSPECT_WEEK, "orders"] == 1071
