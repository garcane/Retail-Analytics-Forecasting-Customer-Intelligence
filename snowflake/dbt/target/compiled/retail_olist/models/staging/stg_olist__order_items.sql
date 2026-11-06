-- Staging: typed view over RAW.ORDER_ITEMS. Port of sql/staging/stg_order_items.sql.
-- Grain: one row per order item (order_id, order_item_id).
-- Money is NUMBER(12,2) so sums are exact. Timestamps are TIMESTAMP_NTZ (DuckDB TIMESTAMP, no time zone).
select
    nullif(order_id, '')                                                                 as order_id,
    cast(nullif(order_item_id, '') as integer)                                           as order_item_id,
    nullif(product_id, '')                                                               as product_id,
    nullif(seller_id, '')                                                                as seller_id,
    to_timestamp_ntz(nullif(shipping_limit_date, ''), 'YYYY-MM-DD HH24:MI:SS')           as shipping_limit_date,
    cast(nullif(price, '') as number(12, 2))                                             as price,
    cast(nullif(freight_value, '') as number(12, 2))                                     as freight_value
from RETAIL_OLIST.RAW.order_items