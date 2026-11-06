-- dim_product: one row per product. Port of sql/dimensions/dim_product.sql.
-- Grain: one row per product_id. Key: product_key (surrogate); -1 = unknown.
-- English category falls back to the Portuguese name when the translation file has no entry (13 products),
-- and both fall back to 'unknown' when the product has no category (610 products).
select
    cast(-1 as bigint)                   as product_key,
    cast('UNKNOWN' as varchar)           as product_id,
    cast('unknown' as varchar)           as product_category_name,
    cast('unknown' as varchar)           as product_category_name_english,
    cast(null as integer)                as product_name_length,
    cast(null as integer)                as product_description_length,
    cast(null as integer)                as product_photos_qty,
    cast(null as integer)                as product_weight_g,
    cast(null as integer)                as product_length_cm,
    cast(null as integer)                as product_height_cm,
    cast(null as integer)                as product_width_cm,
    cast(null as bigint)                 as product_volume_cm3

union all

select
    cast(row_number() over (order by p.product_id) as bigint)                        as product_key,
    p.product_id,
    coalesce(p.product_category_name, 'unknown')                                     as product_category_name,
    coalesce(t.product_category_name_english, p.product_category_name, 'unknown')    as product_category_name_english,
    p.product_name_length,
    p.product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    -- length * height * width; null when any dimension is missing. Widened to bigint before multiplying.
    cast(p.product_length_cm as bigint) * p.product_height_cm * p.product_width_cm   as product_volume_cm3
from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__products p
left join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__category_translation t
    on t.product_category_name = p.product_category_name