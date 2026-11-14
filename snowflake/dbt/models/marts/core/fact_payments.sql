-- fact_payments: one row per payment instalment record. Port of sql/facts/fact_payments.sql.
-- Grain: one row per (order_id, payment_sequential). An order can have up to 29 payments.
-- Payments carry no date of their own, so purchase_date_key is the order's purchase date.
-- payment_value does NOT always equal items + freight (380 of 98,665 orders differ, mostly instalment
-- orders), so revenue is measured from fact_order_items and payments are analysed here, never forced to tie.
select
    p.order_id,
    p.payment_sequential,
    cast(coalesce(dc.customer_key, -1) as bigint)   as customer_key,
    {{ date_key('o.order_purchase_timestamp') }}    as purchase_date_key,
    p.payment_type,
    p.payment_installments,
    p.payment_value
from {{ ref('stg_olist__order_payments') }} p
join {{ ref('stg_olist__orders') }} o
    on o.order_id = p.order_id
left join {{ ref('stg_olist__customers') }} c
    on c.customer_id = o.customer_id
left join {{ ref('dim_customer') }} dc
    on dc.customer_unique_id = c.customer_unique_id
