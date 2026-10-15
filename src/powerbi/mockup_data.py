"""Compact pre-aggregated data for the dashboard mock-up (embedded in DASHBOARD_MOCKUP.html).

The mock-up is a static page, so instead of the 100,000-row facts it carries small cubes that are exact for every slicer
combination the mock-up offers (month range, category, state). Three measures are approximate and are labelled as such
in the page: buying customers over several months (a repeat customer counts once per month), the median delivery time
(computed from a 1-day histogram) and the riskiest-orders list (top 10 per month and state).

    build(db, data_dir) -> dict   (JSON-serialisable)
"""

from __future__ import annotations

from pathlib import Path

import duckdb

import model_spec as ms

SHARES = [5, 10, 15, 20, 25, 30]
HIST_DAYS = 61            # buckets 0..59 days, last bucket = 60+ days
METHODS = ["actual", "naive_last_week", "moving_average_8", "simple_exp_smoothing", "damped_trend", "ar1_trend_26w", "combo_naive_ma8"]


def build(db: Path | None = None, data_dir: Path | None = None) -> dict:
    data = (data_dir or ms.ROOT / "powerbi" / "data").as_posix()
    con = duckdb.connect(str(db or ms.ROOT / "warehouse.duckdb"), read_only=True)

    months = [r[0] for r in con.execute("select distinct d.year_month from fact_orders o join dim_date d on d.date_key = o.purchase_date_key order by 1").fetchall()]
    states = [r[0] for r in con.execute("select distinct g.state from fact_orders o join dim_geography g on g.geography_key = o.customer_geography_key order by 1").fetchall()]
    cats = [r[0] for r in con.execute("select distinct product_category_name_english from dim_product order by 1").fetchall()]
    mi = {m: i for i, m in enumerate(months)}
    si = {s: i for i, s in enumerate(states)}
    ci = {c: i for i, c in enumerate(cats)}

    base = ("from fact_orders o join dim_date d on d.date_key = o.purchase_date_key "
            "join dim_geography g on g.geography_key = o.customer_geography_key")

    # sales by month and state (order grain; items already aggregated onto the order)
    sales = [[mi[m], si[s], int(n), round(float(rev), 2), round(float(frt), 2), int(items), int(cust)] for m, s, n, rev, frt, items, cust in con.execute(
        f"select d.year_month, g.state, count(*), sum(o.items_price), sum(o.items_freight), sum(o.item_count), count(distinct o.customer_key) "
        f"{base} where o.is_net_order group by 1, 2 order by 1, 2".replace("o.is_net_order", "(o.order_status not in ('canceled','unavailable') and o.item_count > 0)")).fetchall()]

    # sales by month, category and state (item grain; item-weighted lateness)
    cube = [[mi[m], ci[c], si[s], int(n), int(items), round(float(rev), 2), round(float(frt), 2), int(late), int(known), int(cust)]
            for m, c, s, n, items, rev, frt, late, known, cust in con.execute(
        """select d.year_month, p.product_category_name_english, g.state,
                  count(distinct oi.order_id), count(*), sum(oi.price), sum(oi.freight_value),
                  count(*) filter (where o.is_late), count(*) filter (where o.is_late is not null), count(distinct oi.customer_key)
           from fact_order_items oi
           join fact_orders o on o.order_id = oi.order_id
           join dim_product p on p.product_key = oi.product_key
           join dim_date d on d.date_key = o.purchase_date_key
           join dim_geography g on g.geography_key = o.customer_geography_key
           where oi.order_status not in ('canceled', 'unavailable')
           group by 1, 2, 3 order by 1, 2, 3""").fetchall()]

    pop = "o.order_status = 'delivered' and o.is_late is not null and not o.has_timestamp_anomaly"
    delivery: dict[tuple[int, int], list] = {}
    for m, s, n, late, promised, under20 in con.execute(
            f"select d.year_month, g.state, count(*), count(*) filter (where o.is_late), sum(date_diff('second', o.purchase_ts, o.estimated_delivery_ts) / 86400.0), "
            f"count(*) filter (where date_diff('second', o.purchase_ts, o.estimated_delivery_ts) / 86400.0 < 20) {base} where {pop} group by 1, 2").fetchall():
        delivery[(mi[m], si[s])] = [mi[m], si[s], int(n), int(late), round(float(promised), 2), int(under20), [0] * HIST_DAYS]
    for m, s, day, n in con.execute(
            f"select d.year_month, g.state, least(floor(o.delivery_days)::int, {HIST_DAYS - 1}), count(*) {base} where {pop} group by 1, 2, 3").fetchall():
        delivery[(mi[m], si[s])][6][day] = int(n)

    reviews = [[mi[m], si[s], int(b), int(n), int(score), int(low)] for m, s, b, n, score, low in con.execute(
        f"""select d.year_month, g.state, o.delay_bucket_order, count(*), sum(r.review_score), count(*) filter (where r.review_score <= 2)
            {base} join fact_reviews r on r.order_id = o.order_id and r.is_latest_review_for_order
            where o.order_status = 'delivered' and o.delivery_delay_days is not null group by 1, 2, 3""".replace("o.delay_bucket_order", """case when o.delivery_delay_days <= 0 then 1
                 when o.delivery_delay_days <= 3 then 2 when o.delivery_delay_days <= 7 then 3 when o.delivery_delay_days <= 14 then 4 else 5 end""")).fetchall()]

    sc = f"read_parquet('{data}/late_delivery_scores.parquet')"
    risk = []
    for m, s, n, late, *flag in con.execute(
            f"select month, customer_state, count(*), sum(is_late), " + ", ".join(
                f"count(*) filter (where risk_percentile > {1 - p / 100}), sum(is_late) filter (where risk_percentile > {1 - p / 100})" for p in SHARES)
            + f" from {sc} group by 1, 2 order by 1, 2").fetchall():
        risk.append([mi[m], si[s], int(n), int(late), [int(x or 0) for x in flag]])
    top: dict[str, list] = {}
    for m, s, oid, score, cat, late in con.execute(
            f"select month, customer_state, order_id, risk_score, category, is_late from (select *, row_number() over (partition by month, customer_state order by risk_score desc) rn from {sc}) where rn <= 10").fetchall():
        top.setdefault(f"{mi[m]}|{si[s]}", []).append([oid, round(float(score), 4), cat, int(late)])

    weeks = [str(r[0]) for r in con.execute(f"select distinct target_week from read_csv('{data}/forecast_backtest.csv', header=true) order by 1").fetchall()]
    wi = {w: i for i, w in enumerate(weeks)}
    forecast = [[0 if t == "orders" else 1, int(h), METHODS.index(meth), wi[str(w)], round(float(f), 2), round(float(a), 2)]
                for t, h, meth, w, f, a in con.execute(
        f"select target, horizon, method, target_week, forecast, actual from read_csv('{data}/forecast_backtest.csv', header=true) order by 1, 2, 3, 4").fetchall()]
    customers_total = con.execute("select count(distinct customer_key) from fact_order_items where order_status not in ('canceled', 'unavailable')").fetchone()[0]
    con.close()
    return {"customers_total": int(customers_total), "months": months, "states": states, "cats": cats, "shares": SHARES, "methods": METHODS, "weeks": weeks,
            "sales": sales, "cube": cube, "delivery": sorted(delivery.values()), "reviews": reviews, "risk": risk, "top": top, "forecast": forecast}
