-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of src/ml/forecast_baseline.py weekly_series (totals must equal the facts). Expectations are derived from the fact tables, never hard-coded.
-- Weeks are Mondays (ISO day 1), and the series covers every order and every item.
with m as (
    select sum(orders) as orders, sum(revenue) as revenue,
           count_if(dayofweekiso(week) != 1) as non_monday_weeks
    from {{ ref('mart_weekly_orders_revenue') }}
), o as (
    select count(*) as orders from {{ ref('fact_orders') }} where purchase_ts is not null
), r as (
    select sum(oi.price) as revenue
    from {{ ref('fact_order_items') }} oi
    join {{ ref('fact_orders') }} f on f.order_id = oi.order_id
    where f.purchase_ts is not null
)
select 'orders' as failed_check, o.orders::float as expected, m.orders::float as actual from o, m where o.orders != m.orders
union all select 'revenue within 0.01', r.revenue::float, m.revenue::float from r, m where abs(r.revenue - m.revenue) > 0.01
union all select 'every week starts on a Monday', 0, m.non_monday_weeks from m where m.non_monday_weeks > 0
