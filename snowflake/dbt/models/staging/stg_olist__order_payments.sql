-- Staging: typed view over RAW.ORDER_PAYMENTS. Port of sql/staging/stg_order_payments.sql.
-- Grain: one row per payment (order_id, payment_sequential).
select
    nullif(order_id, '')                                         as order_id,
    cast(nullif(payment_sequential, '') as integer)              as payment_sequential,
    nullif(payment_type, '')                                     as payment_type,
    cast(nullif(payment_installments, '') as integer)            as payment_installments,
    cast(nullif(payment_value, '') as number(12, 2))             as payment_value
from {{ source('olist_raw', 'order_payments') }}
