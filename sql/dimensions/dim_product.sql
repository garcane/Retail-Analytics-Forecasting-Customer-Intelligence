-- dim_product: one row per product.
-- Grain: one row per product_id. Key: product_key (surrogate); -1 = unknown.
-- English category falls back to the Portuguese name when the translation file has no entry
-- (13 products), and both fall back to 'unknown' when the product has no category (610 products).
create table dim_product (
    product_key                  BIGINT PRIMARY KEY,
    product_id                   VARCHAR NOT NULL UNIQUE,
    product_category_name        VARCHAR,
    product_category_name_english VARCHAR,
    product_name_length          INTEGER,
    product_description_length   INTEGER,
    product_photos_qty           INTEGER,
    product_weight_g             INTEGER,
    product_length_cm            INTEGER,
    product_height_cm            INTEGER,
    product_width_cm             INTEGER,
    product_volume_cm3           BIGINT      -- length * height * width; null when any dimension is missing
);

insert into dim_product values (-1, 'UNKNOWN', 'unknown', 'unknown', null, null, null, null, null, null, null, null);

insert into dim_product
select
    row_number() over (order by p.product_id),
    p.product_id,
    coalesce(p.product_category_name, 'unknown'),
    coalesce(t.product_category_name_english, p.product_category_name, 'unknown'),
    p.product_name_length,
    p.product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    p.product_length_cm::bigint * p.product_height_cm * p.product_width_cm
from stg_products p
left join stg_category_translation t using (product_category_name);
