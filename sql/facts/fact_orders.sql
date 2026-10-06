-- fact_orders: one row per order, including the 775 orders that have no items.
-- Grain: one row per order_id (PK). Order-level process measures: lifecycle dates, delivery time, lateness.
-- Items and payments are pre-aggregated to the order grain BEFORE joining (joining them side by side
-- would repeat rows and overstate item revenue by ~4.5-5%; see notebooks/01_dataset_discovery.ipynb).
-- Missing milestone dates map to date_key -1 (not applicable); the raw timestamps stay nullable.
create table fact_orders (
    order_id                    VARCHAR PRIMARY KEY,
    customer_id                 VARCHAR NOT NULL,   -- degenerate: source per-order customer id
    order_status                VARCHAR NOT NULL,   -- degenerate: 8 values, no dimension needed
    customer_key                BIGINT  NOT NULL REFERENCES dim_customer (customer_key),
    customer_geography_key      BIGINT  NOT NULL REFERENCES dim_geography (geography_key),
    purchase_date_key           INTEGER NOT NULL REFERENCES dim_date (date_key),
    approved_date_key           INTEGER NOT NULL REFERENCES dim_date (date_key),
    carrier_date_key            INTEGER NOT NULL REFERENCES dim_date (date_key),
    delivered_customer_date_key INTEGER NOT NULL REFERENCES dim_date (date_key),
    estimated_delivery_date_key INTEGER NOT NULL REFERENCES dim_date (date_key),
    purchase_ts                 TIMESTAMP NOT NULL,
    approved_ts                 TIMESTAMP,
    carrier_ts                  TIMESTAMP,
    delivered_customer_ts       TIMESTAMP,
    estimated_delivery_ts       TIMESTAMP,
    item_count                  INTEGER NOT NULL,         -- 0 for orders with no items
    items_price                 DECIMAL(12,2) NOT NULL,
    items_freight               DECIMAL(12,2) NOT NULL,
    payment_count               INTEGER NOT NULL,
    payment_total               DECIMAL(12,2) NOT NULL,
    delivery_days               DOUBLE,                   -- purchase -> customer delivery, fractional days
    delivery_delay_days         DOUBLE,                   -- delivered - estimated; positive = late
    is_late                     BOOLEAN,                  -- delivered after the estimate; null if no delivery date
    has_timestamp_anomaly       BOOLEAN NOT NULL          -- carrier before purchase, or customer before carrier
);

insert into fact_orders
with items as (
    select order_id, count(*) as item_count, sum(price) as items_price, sum(freight_value) as items_freight
    from stg_order_items group by 1
),
pay as (
    select order_id, count(*) as payment_count, sum(payment_value) as payment_total
    from stg_order_payments group by 1
)
select
    o.order_id,
    o.customer_id,
    o.order_status,
    coalesce(dc.customer_key, -1),
    coalesce(g.geography_key, -1),
    coalesce(strftime(o.order_purchase_timestamp,      '%Y%m%d')::integer, -1),
    coalesce(strftime(o.order_approved_at,             '%Y%m%d')::integer, -1),
    coalesce(strftime(o.order_delivered_carrier_date,  '%Y%m%d')::integer, -1),
    coalesce(strftime(o.order_delivered_customer_date, '%Y%m%d')::integer, -1),
    coalesce(strftime(o.order_estimated_delivery_date, '%Y%m%d')::integer, -1),
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    coalesce(i.item_count, 0),
    coalesce(i.items_price, 0),
    coalesce(i.items_freight, 0),
    coalesce(p.payment_count, 0),
    coalesce(p.payment_total, 0),
    date_diff('second', o.order_purchase_timestamp, o.order_delivered_customer_date) / 86400.0,
    date_diff('second', o.order_estimated_delivery_date, o.order_delivered_customer_date) / 86400.0,
    o.order_delivered_customer_date > o.order_estimated_delivery_date,
    coalesce(o.order_delivered_carrier_date < o.order_purchase_timestamp, false)
        or coalesce(o.order_delivered_customer_date < o.order_delivered_carrier_date, false)
from stg_orders o
left join stg_customers c  on c.customer_id = o.customer_id
left join dim_customer dc  on dc.customer_unique_id = c.customer_unique_id
left join dim_geography g  on g.zip_prefix = c.customer_zip_code_prefix
left join items i          on i.order_id = o.order_id
left join pay p            on p.order_id = o.order_id;
