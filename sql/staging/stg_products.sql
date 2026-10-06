-- Staging: typed view over the raw products file.
-- Grain: one row per product (product_id).
-- Fixes the source's misspelled columns (lenght -> length); everything else is unchanged.
create or replace view stg_products as
select
    product_id,
    product_category_name,
    product_name_lenght        as product_name_length,
    product_description_lenght as product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from read_csv(
    '${DATA_DIR}/olist_products_dataset.csv',
    header = true,
    columns = {
        'product_id': 'VARCHAR',
        'product_category_name': 'VARCHAR',
        'product_name_lenght': 'INTEGER',
        'product_description_lenght': 'INTEGER',
        'product_photos_qty': 'INTEGER',
        'product_weight_g': 'INTEGER',
        'product_length_cm': 'INTEGER',
        'product_height_cm': 'INTEGER',
        'product_width_cm': 'INTEGER'
    }
);
