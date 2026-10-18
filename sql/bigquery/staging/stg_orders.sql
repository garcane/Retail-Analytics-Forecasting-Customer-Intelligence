-- Staging: typed view over the raw orders file. No cleaning, no re-casing.
-- Grain: one row per order (order_id).
-- BigQuery: the read_csv(columns = {...}) type list becomes a cast per column;
-- TIMESTAMP (no time zone) -> DATETIME (docs/data/DATA_MODEL.md, "Moving to BigQuery").
create or replace view `${PROJECT}.staging.stg_orders` as
select
    order_id,
    customer_id,
    order_status,
    cast(order_purchase_timestamp      as datetime) as order_purchase_timestamp,
    cast(order_approved_at             as datetime) as order_approved_at,
    cast(order_delivered_carrier_date  as datetime) as order_delivered_carrier_date,
    cast(order_delivered_customer_date as datetime) as order_delivered_customer_date,
    cast(order_estimated_delivery_date as datetime) as order_estimated_delivery_date
from `${PROJECT}.raw.olist_orders_dataset`;