-- mart_state_performance: port of sql/analytics/03_state_performance.sql (reports/analytics/03_*.csv).
-- Grain: one row per customer state. Order grain from fact_orders (items already aggregated, so no fan-out);
-- canceled/unavailable orders and orders without items are excluded. Delivery figures use delivered orders only.
-- Consumers must ORDER BY net_revenue DESC.
--
-- Snowflake notes: operands cast ::float before division/AVG; NULL-preserving boolean cast; MEDIAN of a float.
select g.state                                                                                  as customer_state,
       count(*)                                                                                 as orders,
       round(sum(o.items_price), 2)                                                             as net_revenue,
       round(100 * sum(o.items_price)::float / sum(sum(o.items_price)::float) over (), 2)       as revenue_share_pct,
       round(sum(o.items_price)::float / count(*), 2)                                           as avg_order_value,
       round(100 * sum(o.items_freight)::float / nullif(sum(o.items_price)::float, 0), 1)       as freight_pct_of_price,
       count(o.is_late)                                                                         as delivered_orders,
       round(100 * avg((case when o.is_late then 1 when not o.is_late then 0 end)::float), 1)   as late_pct,
       round(median(o.delivery_days), 1)                                                        as median_delivery_days
from {{ ref('fact_orders') }} o
join {{ ref('dim_geography') }} g on g.geography_key = o.customer_geography_key
where o.order_status not in ('canceled', 'unavailable') and o.item_count > 0
group by g.state
order by net_revenue desc nulls last
