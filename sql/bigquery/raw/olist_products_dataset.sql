-- Raw: external table over the immutable products CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_products.sql.
-- The source's misspelled names (product_name_lenght, product_description_lenght) are
-- kept here; staging.stg_products renames them, exactly like the local view does.
create or replace external table `${PROJECT}.raw.olist_products_dataset` (
    product_id                  string,
    product_category_name       string,
    product_name_lenght         string,  -- INT64 as product_name_length in staging
    product_description_lenght  string,  -- INT64 as product_description_length in staging
    product_photos_qty          string,
    product_weight_g            string,
    product_length_cm           string,
    product_height_cm           string,
    product_width_cm            string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_products_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);