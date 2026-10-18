-- Staging: typed view over the raw products file.
-- Grain: one row per product (product_id).
-- Fixes the source's misspelled columns (lenght -> length); everything else is unchanged.
create or replace view `${PROJECT}.staging.stg_products` as
select
    product_id,
    product_category_name,
    cast(product_name_lenght        as int64) as product_name_length,
    cast(product_description_lenght as int64) as product_description_length,
    cast(product_photos_qty         as int64) as product_photos_qty,
    cast(product_weight_g           as int64) as product_weight_g,
    cast(product_length_cm          as int64) as product_length_cm,
    cast(product_height_cm          as int64) as product_height_cm,
    cast(product_width_cm           as int64) as product_width_cm
from `${PROJECT}.raw.olist_products_dataset`;