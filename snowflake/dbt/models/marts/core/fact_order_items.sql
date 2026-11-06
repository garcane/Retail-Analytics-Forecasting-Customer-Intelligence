-- fact_order_items: the core sales fact. Port of sql/facts/fact_order_items.sql.
-- Grain: one row per order item (order_id, order_item_id). All item revenue lives here.
-- Count orders with count(distinct order_id): an order has up to 21 item rows.
-- order_status is copied onto the row so revenue can be filtered by status without joining another fact.
-- Unmatched dimension lookups map to the -1 unknown member; missing dates to date_key -1.
select
    i.order_id,
    i.order_item_id,
    o.order_status,
    cast(coalesce(dc.customer_key, -1) as bigint)        as customer_key,
    cast(coalesce(dp.product_key, -1) as bigint)         as product_key,
    cast(coalesce(ds.seller_key, -1) as bigint)          as seller_key,
    cast(coalesce(gc.geography_key, -1) as bigint)       as customer_geography_key,
    cast(coalesce(gs.geography_key, -1) as bigint)       as seller_geography_key,
    {{ date_key('o.order_purchase_timestamp') }}         as purchase_date_key,
    {{ date_key('i.shipping_limit_date') }}              as shipping_limit_date_key,
    i.price,
    i.freight_value,
    cast(i.price + i.freight_value as number(12, 2))     as item_total_value   -- price + freight_value
from {{ ref('stg_olist__order_items') }} i
join {{ ref('stg_olist__orders') }} o
    on o.order_id = i.order_id
left join {{ ref('stg_olist__customers') }} c
    on c.customer_id = o.customer_id
left join {{ ref('dim_customer') }} dc
    on dc.customer_unique_id = c.customer_unique_id
left join {{ ref('dim_product') }} dp
    on dp.product_id = i.product_id
left join {{ ref('dim_seller') }} ds
    on ds.seller_id = i.seller_id
left join {{ ref('stg_olist__sellers') }} s
    on s.seller_id = i.seller_id
left join {{ ref('dim_geography') }} gc
    on gc.zip_prefix = c.customer_zip_code_prefix
left join {{ ref('dim_geography') }} gs
    on gs.zip_prefix = s.seller_zip_code_prefix
