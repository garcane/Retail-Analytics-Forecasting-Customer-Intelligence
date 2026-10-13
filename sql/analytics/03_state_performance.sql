-- Customer-state performance from fact_orders (order grain; items already aggregated, DD-01). Orders that were canceled
-- or unavailable are excluded. Delivery figures use delivered orders only.
select g.state                                                                as customer_state,
       count(*)                                                               as orders,
       round(sum(o.items_price), 2)                                           as net_revenue,
       round(100 * sum(o.items_price) / sum(sum(o.items_price)) over (), 2)   as revenue_share_pct,
       round(sum(o.items_price) / count(*), 2)                                as avg_order_value,
       round(100 * sum(o.items_freight) / nullif(sum(o.items_price), 0), 1)   as freight_pct_of_price,
       count(o.is_late)                                                       as delivered_orders,
       round(100 * avg(o.is_late::integer), 1)                                as late_pct,
       round(median(o.delivery_days), 1)                                      as median_delivery_days
from fact_orders o
join dim_geography g on g.geography_key = o.customer_geography_key
where o.order_status not in ('canceled', 'unavailable') and o.item_count > 0
group by g.state
order by net_revenue desc;
