-- int_order_items_agg: order items pre-aggregated to the ORDER grain, BEFORE they are joined to anything else.
-- Joining items and payments side by side would repeat rows and overstate item revenue by ~4.5-5%
-- (see sql/facts/fact_orders.sql). Grain: one row per order_id that has at least one item.
select
    order_id,
    cast(count(*) as integer)                  as item_count,
    cast(sum(price) as number(12, 2))          as items_price,
    cast(sum(freight_value) as number(12, 2))  as items_freight
from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_items
group by order_id