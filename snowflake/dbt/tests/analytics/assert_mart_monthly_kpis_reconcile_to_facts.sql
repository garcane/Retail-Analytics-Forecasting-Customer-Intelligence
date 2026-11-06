-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_monthly_kpis_add_up_to_net_revenue. Expectations are derived from the fact tables, never hard-coded.
with net as (
    select sum(price) as revenue, count(distinct order_id) as orders, count(*) as items
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
), m as (
    select sum(net_revenue) as revenue, sum(orders) as orders, sum(items) as items, count(*) as n_rows, count(distinct year_month) as n_months
    from {{ ref('mart_monthly_kpis') }}
)
select 'net_revenue within 0.5' as failed_check, net.revenue::float as expected, m.revenue::float as actual from net, m where abs(net.revenue - m.revenue) > 0.5
union all select 'orders', net.orders, m.orders from net, m where net.orders != m.orders
union all select 'items', net.items, m.items from net, m where net.items != m.items
union all select 'year_month unique', m.n_rows, m.n_months from m where m.n_rows != m.n_months
