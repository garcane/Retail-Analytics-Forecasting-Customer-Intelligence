-- Category performance, item-weighted: each item row carries its order's lateness and its order's latest review.
-- Reviews are restricted to one per order (is_latest_review_for_order), so joining them does not repeat item rows.
with item_rows as (
    select p.product_category_name_english as category,
           oi.order_id, oi.price, oi.freight_value, o.is_late, r.review_score
    from fact_order_items oi
    join dim_product p on p.product_key = oi.product_key
    join fact_orders o on o.order_id = oi.order_id
    left join fact_reviews r on r.order_id = oi.order_id and r.is_latest_review_for_order
    where oi.order_status not in ('canceled', 'unavailable')
), by_category as (
    select category,
           count(distinct order_id)        as orders,
           count(*)                        as items,
           sum(price)                      as revenue,
           avg(price)                      as avg_item_price,
           sum(freight_value) / sum(price) as freight_to_price,
           avg(is_late::integer)           as late_rate,
           avg(review_score)               as avg_review_score
    from item_rows group by category
)
select category, orders, items,
       round(revenue, 2)                                                                            as net_revenue,
       round(100 * revenue / sum(revenue) over (), 2)                                               as revenue_share_pct,
       round(100 * sum(revenue) over (order by revenue desc, category) / sum(revenue) over (), 2)   as cumulative_share_pct,
       round(avg_item_price, 2)                                                                     as avg_item_price,
       round(100 * freight_to_price, 1)                                                             as freight_pct_of_price,
       round(100 * late_rate, 1)                                                                    as late_pct,
       round(avg_review_score, 2)                                                                   as avg_review_score
from by_category
order by revenue desc, category;
