-- int_customers_latest: one row per real customer (customer_unique_id) with location attributes taken from
-- the customer's most recent order (type-1). Logic lifted from sql/dimensions/dim_customer.sql.
-- customer_id is per ORDER in the source, so it is only used here to find the latest order.
-- Tie-break (identical to DuckDB): latest purchase timestamp first, NULL purchase timestamps last
-- (explicit NULLS LAST: Snowflake would otherwise put NULLs first under DESC), then customer_id ascending.
with ranked as (
    select
        c.customer_unique_id,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        row_number() over (
            partition by c.customer_unique_id
            order by o.order_purchase_timestamp desc nulls last, c.customer_id
        ) as rn
    from {{ ref('stg_olist__customers') }} c
    left join {{ ref('stg_olist__orders') }} o
        on o.customer_id = c.customer_id
)

select
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from ranked
where rn = 1
