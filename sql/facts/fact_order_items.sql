-- fact_order_items: the core sales fact.
-- Grain: one row per order item (order_id, order_item_id). All item revenue lives here.
-- Count orders with count(distinct order_id): an order has up to 21 item rows.
-- order_status is copied onto the row so revenue can be filtered by status without joining another fact.
create table fact_order_items (
    order_id               VARCHAR NOT NULL,   -- degenerate
    order_item_id          INTEGER NOT NULL,   -- degenerate: position of the item within the order
    order_status           VARCHAR NOT NULL,
    customer_key           BIGINT  NOT NULL REFERENCES dim_customer (customer_key),
    product_key            BIGINT  NOT NULL REFERENCES dim_product (product_key),
    seller_key             BIGINT  NOT NULL REFERENCES dim_seller (seller_key),
    customer_geography_key BIGINT  NOT NULL REFERENCES dim_geography (geography_key),
    seller_geography_key   BIGINT  NOT NULL REFERENCES dim_geography (geography_key),
    purchase_date_key      INTEGER NOT NULL REFERENCES dim_date (date_key),
    shipping_limit_date_key INTEGER NOT NULL REFERENCES dim_date (date_key),
    price                  DECIMAL(12,2) NOT NULL,
    freight_value          DECIMAL(12,2) NOT NULL,
    item_total_value       DECIMAL(12,2) NOT NULL,   -- price + freight_value
    PRIMARY KEY (order_id, order_item_id)
);

insert into fact_order_items
select
    i.order_id,
    i.order_item_id,
    o.order_status,
    coalesce(dc.customer_key, -1),
    coalesce(dp.product_key, -1),
    coalesce(ds.seller_key, -1),
    coalesce(gc.geography_key, -1),
    coalesce(gs.geography_key, -1),
    coalesce(strftime(o.order_purchase_timestamp, '%Y%m%d')::integer, -1),
    coalesce(strftime(i.shipping_limit_date,      '%Y%m%d')::integer, -1),
    i.price,
    i.freight_value,
    i.price + i.freight_value
from stg_order_items i
join stg_orders o          on o.order_id = i.order_id
left join stg_customers c  on c.customer_id = o.customer_id
left join dim_customer dc  on dc.customer_unique_id = c.customer_unique_id
left join dim_product dp   on dp.product_id = i.product_id
left join dim_seller ds    on ds.seller_id = i.seller_id
left join stg_sellers s    on s.seller_id = i.seller_id
left join dim_geography gc on gc.zip_prefix = c.customer_zip_code_prefix
left join dim_geography gs on gs.zip_prefix = s.seller_zip_code_prefix;
