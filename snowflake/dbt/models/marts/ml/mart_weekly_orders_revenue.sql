-- mart_weekly_orders_revenue: port of the weekly_series() SQL in src/ml/forecast_baseline.py.
-- Grain: one row per ISO week (Monday start) that has at least one order, by purchase date.
--   week     DATE     Monday of the ISO week of purchase_ts
--   orders   integer  orders purchased that week (fact_orders, every status)
--   revenue  float    sum of item price that week (fact_order_items, DD-04), 0 when the week has orders but no items
-- Consumers must ORDER BY week (src/data_access does).
--
-- Snowflake notes: the Monday is computed with the iso_week_start macro (explicit dayofweekiso arithmetic), so the
-- result never depends on the WEEK_START session parameter; revenue is ::float to match DuckDB's DOUBLE.
with orders as (
    select {{ iso_week_start('purchase_ts') }} as week, count(*) as orders
    from {{ ref('fact_orders') }}
    group by 1
), revenue as (
    select {{ iso_week_start('o.purchase_ts') }} as week, sum(oi.price)::float as revenue
    from {{ ref('fact_order_items') }} oi
    join {{ ref('fact_orders') }} o on o.order_id = oi.order_id
    group by 1
)
select orders.week as week,
       orders.orders as orders,
       coalesce(revenue.revenue, 0) as revenue
from orders
left join revenue on revenue.week = orders.week
order by week
