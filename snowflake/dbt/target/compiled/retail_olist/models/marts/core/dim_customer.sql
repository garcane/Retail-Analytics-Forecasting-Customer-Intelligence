-- dim_customer: one row per real customer (customer_unique_id). Port of sql/dimensions/dim_customer.sql.
-- Grain: one row per customer_unique_id. Key: customer_key (surrogate); -1 = unknown.
-- The source customer_id is per ORDER (99,441 ids for 96,096 people), so it is not used as the grain.
-- Location attributes come from the customer's most recent order (type-1, see int_customers_latest).
-- The location AT THE TIME of each order is carried on the facts via dim_geography.
-- Surrogate key = row_number() ordered by customer_unique_id (binary order, as in DuckDB).
select
    cast(-1 as bigint)                         as customer_key,
    cast('UNKNOWN' as varchar)                 as customer_unique_id,
    cast(null as varchar)                      as customer_zip_code_prefix,
    cast('Unknown' as varchar)                 as customer_city,
    cast('Unknown' as varchar)                 as customer_state

union all

select
    cast(row_number() over (order by customer_unique_id) as bigint) as customer_key,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from RETAIL_OLIST.DBT_CI_INTERMEDIATE.int_customers_latest