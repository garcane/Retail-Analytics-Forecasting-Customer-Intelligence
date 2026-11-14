-- mart_category_performance: port of sql/analytics/02_category_performance.sql (reports/analytics/02_*.csv).
-- Grain: one row per English product category. Item-weighted: each item row carries its order's lateness and its
-- order's latest review (one review per order, so the join does not repeat item rows).
-- Consumers must ORDER BY net_revenue DESC, category.
--
-- Snowflake notes
--   * boolean averages: case when ... then 1 when not ... then 0 end keeps NULL (IFF would turn NULL into 0)
--   * every averaged/divided operand is cast ::float, EXCEPT avg_item_price: it is exact NUMBER arithmetic,
--     sum(price) / count(price) (Snowflake keeps >= 6 fractional digits), then round(..., 2) rounds half away from zero.
--     Two categories sit exactly on a .xx5 boundary in the DuckDB reference: security_and_services (141.645 -> 141.65)
--     and la_cuisine (146.785 -> 146.79, whose double is 146.78499999999999659 and would round DOWN under float
--     arithmetic). Exact division keeps both on the reference value. The offline simulation (sqlglot -> DuckDB) cannot
--     prove Snowflake's NUMBER rounding: UNVERIFIED, listed in README_LIVE_CHECKS.md.
--   * NULLS LAST on every ORDER BY (Snowflake sorts NULLs first under DESC, DuckDB last)
with item_rows as (
    select p.product_category_name_english as category,
           oi.order_id, oi.price, oi.freight_value, o.is_late, r.review_score
    from {{ ref('fact_order_items') }} oi
    join {{ ref('dim_product') }} p on p.product_key = oi.product_key
    join {{ ref('fact_orders') }} o on o.order_id = oi.order_id
    left join {{ ref('fact_reviews') }} r on r.order_id = oi.order_id and r.is_latest_review_for_order
    where oi.order_status not in ('canceled', 'unavailable')
), by_category as (
    select category,
           count(distinct order_id)                       as orders,
           count(*)                                       as items,
           sum(price)                                     as revenue,
           sum(price) / count(price)                      as avg_item_price,
           sum(freight_value)::float / sum(price)::float  as freight_to_price,
           avg((case when is_late then 1 when not is_late then 0 end)::float) as late_rate,
           avg(review_score::float)                       as avg_review_score
    from item_rows group by category
)
select category, orders, items,
       round(revenue, 2)                                                                                                              as net_revenue,
       round(100 * revenue::float / (sum(revenue) over ())::float, 2)                                                                   as revenue_share_pct,
       round(100 * (sum(revenue) over (order by revenue desc nulls last, category nulls last))::float / (sum(revenue) over ())::float, 2) as cumulative_share_pct,
       round(avg_item_price, 2)                                                                                                       as avg_item_price,
       round(100 * freight_to_price, 1)                                                                                               as freight_pct_of_price,
       round(100 * late_rate, 1)                                                                                                      as late_pct,
       round(avg_review_score, 2)                                                                                                     as avg_review_score
from by_category
order by revenue desc nulls last, category nulls last
