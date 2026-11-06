-- dim_seller: one row per seller. Port of sql/dimensions/dim_seller.sql.
-- Grain: one row per seller_id. Key: seller_key (surrogate); -1 = unknown.
select
    cast(-1 as bigint)                   as seller_key,
    cast('UNKNOWN' as varchar)           as seller_id,
    cast(null as varchar)                as seller_zip_code_prefix,
    cast('Unknown' as varchar)           as seller_city,
    cast('Unknown' as varchar)           as seller_state

union all

select
    cast(row_number() over (order by seller_id) as bigint) as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__sellers