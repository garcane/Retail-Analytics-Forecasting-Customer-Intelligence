-- Staging: typed view over the raw order payments file.
-- Grain: one row per payment (order_id, payment_sequential).
create or replace view `${PROJECT}.staging.stg_order_payments` as
select
    order_id,
    cast(payment_sequential   as int64)   as payment_sequential,
    payment_type,
    cast(payment_installments as int64)   as payment_installments,
    cast(payment_value        as numeric) as payment_value
from `${PROJECT}.raw.olist_order_payments_dataset`;