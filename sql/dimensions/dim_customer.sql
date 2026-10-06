-- dim_customer: one row per real customer (customer_unique_id).
-- Grain: one row per customer_unique_id. Key: customer_key (surrogate); -1 = unknown.
-- The source customer_id is per ORDER (99,441 ids for 96,096 people), so it is not used as the grain.
-- Location attributes come from the customer's most recent order (type-1). The location AT THE TIME of
-- each order is carried on the facts via dim_geography.
create table dim_customer (
    customer_key             BIGINT PRIMARY KEY,
    customer_unique_id       VARCHAR NOT NULL UNIQUE,
    customer_zip_code_prefix VARCHAR,
    customer_city            VARCHAR,
    customer_state           VARCHAR
);

insert into dim_customer values (-1, 'UNKNOWN', null, 'Unknown', 'Unknown');

insert into dim_customer
with latest as (
    select c.customer_unique_id,
           c.customer_zip_code_prefix,
           c.customer_city,
           c.customer_state,
           row_number() over (
               partition by c.customer_unique_id
               order by o.order_purchase_timestamp desc, c.customer_id
           ) as rn
    from stg_customers c
    left join stg_orders o using (customer_id)
)
select row_number() over (order by customer_unique_id),
       customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
from latest
where rn = 1;
