-- int_order_payments_agg: payments pre-aggregated to the ORDER grain (see int_order_items_agg for why).
-- Grain: one row per order_id that has at least one payment record.
select
    order_id,
    cast(count(*) as integer)                  as payment_count,
    cast(sum(payment_value) as number(12, 2))  as payment_total
from {{ ref('stg_olist__order_payments') }}
group by order_id
