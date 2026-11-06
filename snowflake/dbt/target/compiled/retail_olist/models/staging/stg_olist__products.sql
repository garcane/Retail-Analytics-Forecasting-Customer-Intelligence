-- Staging: typed view over RAW.PRODUCTS. Port of sql/staging/stg_products.sql.
-- Grain: one row per product (product_id).
-- Fixes the source's misspelled columns (lenght -> length) exactly as the DuckDB staging view does;
-- everything else is unchanged. The RAW table keeps the source spelling.
select
    nullif(product_id, '')                                              as product_id,
    nullif(product_category_name, '')                                   as product_category_name,
    cast(nullif(product_name_lenght, '') as integer)                    as product_name_length,
    cast(nullif(product_description_lenght, '') as integer)             as product_description_length,
    cast(nullif(product_photos_qty, '') as integer)                     as product_photos_qty,
    cast(nullif(product_weight_g, '') as integer)                       as product_weight_g,
    cast(nullif(product_length_cm, '') as integer)                      as product_length_cm,
    cast(nullif(product_height_cm, '') as integer)                      as product_height_cm,
    cast(nullif(product_width_cm, '') as integer)                       as product_width_cm
from RETAIL_OLIST.RAW.products