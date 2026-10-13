"""Every analytics table must reconcile to the fact tables. Needs the built warehouse (skipped otherwise)."""

import pytest

from conftest import ROOT

pytestmark = pytest.mark.warehouse

EXCLUDED = "('canceled', 'unavailable')"


def table(con, name):
    return con.execute((ROOT / "sql" / "analytics" / f"{name}.sql").read_text(encoding="utf-8")).df()


@pytest.fixture(scope="module")
def net(warehouse):
    revenue, orders, items = warehouse.execute(
        f"select sum(price), count(distinct order_id), count(*) from fact_order_items where order_status not in {EXCLUDED}"
    ).fetchone()
    return {"revenue": float(revenue), "orders": int(orders), "items": int(items)}


def test_monthly_kpis_add_up_to_net_revenue(warehouse, net):
    df = table(warehouse, "01_monthly_kpis")
    assert df["net_revenue"].sum() == pytest.approx(net["revenue"], abs=0.5)
    assert df["orders"].sum() == net["orders"] and df["items"].sum() == net["items"]
    assert df["year_month"].is_unique


def test_monthly_growth_is_blank_next_to_thin_months(warehouse):
    df = table(warehouse, "01_monthly_kpis").reset_index(drop=True)
    for i, row in df.iterrows():
        previous_thin = i == 0 or bool(df.loc[i - 1, "thin_month"])
        if row["thin_month"] or previous_thin:
            assert df.isna().loc[i, "revenue_mom_pct"]


def test_category_revenue_matches_and_shares_are_consistent(warehouse, net):
    df = table(warehouse, "02_category_performance")
    assert df["net_revenue"].sum() == pytest.approx(net["revenue"], abs=0.5)
    assert df["items"].sum() == net["items"]
    assert df["revenue_share_pct"].sum() == pytest.approx(100, abs=0.2)
    assert df["cumulative_share_pct"].iloc[-1] == pytest.approx(100, abs=0.05)
    assert df["cumulative_share_pct"].is_monotonic_increasing


def test_state_table_matches_order_level_totals(warehouse, net):
    df = table(warehouse, "03_state_performance")
    assert df["net_revenue"].sum() == pytest.approx(net["revenue"], abs=0.5)
    assert df["orders"].sum() == net["orders"]
    assert df["late_pct"].between(0, 100).all()


def test_seller_concentration_is_ordered(warehouse):
    df = table(warehouse, "04_seller_concentration").set_index("metric")["value"]
    top1, top10 = df["top 1 seller share of revenue (%)"], df["top 10 sellers share of revenue (%)"]
    top10pct, top50pct = df["top 10% of sellers share of revenue (%)"], df["top 50% of sellers share of revenue (%)"]
    assert 0 < top1 < top10 < 100
    assert top10pct < top50pct <= 100
    assert df["sellers with net revenue"] > 3000


def test_delay_buckets_cover_every_reviewed_delivered_order(warehouse):
    df = table(warehouse, "05_delivery_vs_reviews")
    expected = warehouse.execute(
        """select count(*) from fact_orders o
           join fact_reviews r on r.order_id = o.order_id and r.is_latest_review_for_order
           where o.order_status = 'delivered' and o.delivery_delay_days is not null"""
    ).fetchone()[0]
    assert df["orders"].sum() == expected
    assert df["share_of_orders_pct"].sum() == pytest.approx(100, abs=0.2)
    assert list(df["delay_group"])[0] == "on time or early"  # ordered by severity, not alphabetically
    assert df["avg_review_score"].is_monotonic_decreasing


def test_payment_shares_add_up_and_total_matches_the_fact(warehouse):
    df = table(warehouse, "06_payments")
    total = warehouse.execute("select sum(payment_value) from fact_payments").fetchone()[0]
    assert df["payment_value"].sum() == pytest.approx(float(total), abs=0.5)
    assert df["value_share_pct"].sum() == pytest.approx(100, abs=0.3)


def test_repeat_customer_table_matches_distinct_customers_and_revenue(warehouse):
    df = table(warehouse, "07_repeat_customers")
    customers, revenue = warehouse.execute(
        f"""select count(distinct customer_key), sum(items_price) from fact_orders
            where order_status not in {EXCLUDED} and item_count > 0 and customer_key <> -1"""
    ).fetchone()
    assert df["customers"].sum() == customers
    assert df["net_revenue"].sum() == pytest.approx(float(revenue), abs=0.5)
    assert df.set_index("orders_placed").loc["1", "customer_share_pct"] > 90


def test_delivery_trend_covers_the_same_population_as_the_ml_features(warehouse):
    df = table(warehouse, "08_delivery_trend")
    expected = warehouse.execute(
        "select count(*) from fact_orders where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly"
    ).fetchone()[0]
    assert df["delivered_orders"].sum() == expected
    assert df["purchase_month"].is_unique
