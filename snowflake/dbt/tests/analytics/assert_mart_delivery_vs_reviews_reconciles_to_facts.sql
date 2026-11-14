-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_delay_buckets_cover_every_reviewed_delivered_order. Expectations are derived from the fact tables, never hard-coded.
with expected as (
    select count(*) as orders
    from {{ ref('fact_orders') }} o
    join {{ ref('fact_reviews') }} r on r.order_id = o.order_id and r.is_latest_review_for_order
    where o.order_status = 'delivered' and o.delivery_delay_days is not null
), m as (
    select sum(orders) as orders, sum(share_of_orders_pct) as share_sum, count(*) as n_groups
    from {{ ref('mart_delivery_vs_reviews') }}
), ordered as (
    select avg_review_score,
           lag(avg_review_score) over (order by case delay_group
               when 'on time or early' then 1 when '1-3 days late' then 2 when '4-7 days late' then 3
               when '8-14 days late' then 4 else 5 end) as previous
    from {{ ref('mart_delivery_vs_reviews') }}
)
select 'orders equal reviewed delivered orders' as failed_check, expected.orders::float as expected, m.orders::float as actual from expected, m where expected.orders != m.orders
union all select 'shares add up to 100 (+-0.2)', 100, m.share_sum from m where abs(m.share_sum - 100) > 0.2
union all select 'five delay groups', 5, m.n_groups from m where m.n_groups != 5
union all select 'average review score falls as delay grows', previous, avg_review_score from ordered where avg_review_score > previous
