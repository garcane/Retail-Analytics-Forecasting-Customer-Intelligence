-- Staging: typed view over RAW.CUSTOMERS. Port of sql/staging/stg_customers.sql.
-- Grain: one row per customer_id, which is per ORDER. customer_unique_id identifies the person.
-- Zip prefixes stay VARCHAR so leading zeros survive.
-- nullif(col, '') mirrors DuckDB read_csv, which reads an empty field as NULL whatever the loader did.
select
    nullif(customer_id, '')               as customer_id,
    nullif(customer_unique_id, '')        as customer_unique_id,
    nullif(customer_zip_code_prefix, '')  as customer_zip_code_prefix,
    nullif(customer_city, '')             as customer_city,
    nullif(customer_state, '')            as customer_state
from RETAIL_OLIST.RAW.customers