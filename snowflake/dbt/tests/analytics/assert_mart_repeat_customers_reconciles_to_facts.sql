-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_repeat_customer_table_matches_distinct_customers_and_revenue. Expectations are derived from the fact tables, never hard-coded.
with expected as (
    select count(distinct customer_key) as customers, sum(items_price) as revenue
    from {{ ref('fact_orders') }}
    where order_status not in ('canceled', 'unavailable') and item_count > 0 and customer_key <> -1
), m as (
    select sum(customers) as customers, sum(net_revenue) as revenue
    from {{ ref('mart_repeat_customers') }}
), one_time as (
    select customer_share_pct from {{ ref('mart_repeat_customers') }} where orders_placed = '1'
)
select 'customers' as failed_check, expected.customers::float as expected, m.customers::float as actual from expected, m where expected.customers != m.customers
union all select 'net_revenue within 0.5', expected.revenue::float, m.revenue::float from expected, m where abs(expected.revenue - m.revenue) > 0.5
union all select 'one-time buyers are the majority (> 90%)', 90, customer_share_pct from one_time where customer_share_pct <= 90
