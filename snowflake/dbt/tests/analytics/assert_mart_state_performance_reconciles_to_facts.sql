-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_state_table_matches_order_level_totals. Expectations are derived from the fact tables, never hard-coded.
with net as (
    select sum(price) as revenue, count(distinct order_id) as orders
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
), m as (
    select sum(net_revenue) as revenue, sum(orders) as orders
    from {{ ref('mart_state_performance') }}
)
select 'net_revenue within 0.5' as failed_check, net.revenue::float as expected, m.revenue::float as actual from net, m where abs(net.revenue - m.revenue) > 0.5
union all select 'orders', net.orders, m.orders from net, m where net.orders != m.orders
