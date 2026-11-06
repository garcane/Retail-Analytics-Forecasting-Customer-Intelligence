-- Staging: typed view over RAW.ORDERS. Port of sql/staging/stg_orders.sql. No cleaning, no re-casing.
-- Grain: one row per order (order_id).
select
    nullif(order_id, '')                                                                        as order_id,
    nullif(customer_id, '')                                                                     as customer_id,
    nullif(order_status, '')                                                                    as order_status,
    to_timestamp_ntz(nullif(order_purchase_timestamp, ''), 'YYYY-MM-DD HH24:MI:SS')             as order_purchase_timestamp,
    to_timestamp_ntz(nullif(order_approved_at, ''), 'YYYY-MM-DD HH24:MI:SS')                    as order_approved_at,
    to_timestamp_ntz(nullif(order_delivered_carrier_date, ''), 'YYYY-MM-DD HH24:MI:SS')         as order_delivered_carrier_date,
    to_timestamp_ntz(nullif(order_delivered_customer_date, ''), 'YYYY-MM-DD HH24:MI:SS')        as order_delivered_customer_date,
    to_timestamp_ntz(nullif(order_estimated_delivery_date, ''), 'YYYY-MM-DD HH24:MI:SS')        as order_estimated_delivery_date
from {{ source('olist_raw', 'orders') }}
