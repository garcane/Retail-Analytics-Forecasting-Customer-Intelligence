-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_category_revenue_matches_and_shares_are_consistent. Expectations are derived from the fact tables, never hard-coded.
with net as (
    select sum(price) as revenue, count(*) as items
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
), m as (
    select sum(net_revenue) as revenue, sum(items) as items, sum(revenue_share_pct) as share_sum,
           max(cumulative_share_pct) as last_cumulative
    from {{ ref('mart_category_performance') }}
), c as (
    select count(*) as not_increasing
    from (
        select cumulative_share_pct,
               lag(cumulative_share_pct) over (order by net_revenue desc nulls last, category nulls last) as previous
        from {{ ref('mart_category_performance') }}
    )
    where cumulative_share_pct < previous
)
select 'net_revenue within 0.5' as failed_check, net.revenue::float as expected, m.revenue::float as actual from net, m where abs(net.revenue - m.revenue) > 0.5
union all select 'items', net.items, m.items from net, m where net.items != m.items
union all select 'revenue shares add up to 100 (+-0.2)', 100, m.share_sum from m where abs(m.share_sum - 100) > 0.2
union all select 'cumulative share ends at 100 (+-0.05)', 100, m.last_cumulative from m where abs(m.last_cumulative - 100) > 0.05
union all select 'cumulative share is non-decreasing', 0, c.not_increasing from c where c.not_increasing > 0
