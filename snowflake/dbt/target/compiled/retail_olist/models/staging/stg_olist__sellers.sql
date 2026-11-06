-- Staging: typed view over RAW.SELLERS. Port of sql/staging/stg_sellers.sql.
-- Grain: one row per seller (seller_id). Zip prefix stays text (leading zeros).
select
    nullif(seller_id, '')                as seller_id,
    nullif(seller_zip_code_prefix, '')   as seller_zip_code_prefix,
    nullif(seller_city, '')              as seller_city,
    nullif(seller_state, '')             as seller_state
from RETAIL_OLIST.RAW.sellers