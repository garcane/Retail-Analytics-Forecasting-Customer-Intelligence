-- Staging: typed view over the raw order items file.
-- Grain: one row per order item (order_id, order_item_id).
-- Money is read as NUMERIC (DECIMAL(12,2) -> NUMERIC) so sums are exact.
create or replace view `${PROJECT}.staging.stg_order_items` as
select
    order_id,
    cast(order_item_id       as int64)    as order_item_id,
    product_id,
    seller_id,
    cast(shipping_limit_date as datetime) as shipping_limit_date,
    cast(price               as numeric)  as price,
    cast(freight_value       as numeric)  as freight_value
from `${PROJECT}.raw.olist_order_items_dataset`;