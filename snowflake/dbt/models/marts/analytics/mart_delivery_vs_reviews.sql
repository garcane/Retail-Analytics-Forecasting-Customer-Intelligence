-- mart_delivery_vs_reviews: port of sql/analytics/05_delivery_vs_reviews.sql (reports/analytics/05_*.csv).
-- Grain: one row per delay group (5). One latest review per order, delivered orders with a delivery delay only.
-- An association, not a cause. Severity order (consumers must sort by it; the table stores no row order):
-- on time or early, 1-3 days late, 4-7 days late, 8-14 days late, more than 14 days late.
with delivered as (
    select o.order_id, o.delivery_delay_days, r.review_score
    from {{ ref('fact_orders') }} o
    join {{ ref('fact_reviews') }} r on r.order_id = o.order_id and r.is_latest_review_for_order
    where o.order_status = 'delivered' and o.delivery_delay_days is not null
), bucketed as (
    select *, case when delivery_delay_days <= 0  then '1 on time or early'
                   when delivery_delay_days <= 3  then '2 1-3 days late'
                   when delivery_delay_days <= 7  then '3 4-7 days late'
                   when delivery_delay_days <= 14 then '4 8-14 days late'
                   else '5 more than 14 days late' end as delay_bucket
    from delivered
)
select substr(delay_bucket, 3)                                      as delay_group,
       count(*)                                                     as orders,
       round(100.0 * count(*)::float / sum(count(*)) over (), 1)    as share_of_orders_pct,
       round(avg(review_score::float), 2)                           as avg_review_score,
       round(100 * avg((case when review_score <= 2 then 1 when review_score > 2 then 0 end)::float), 1) as low_score_pct
from bucketed
group by delay_bucket
order by delay_bucket
