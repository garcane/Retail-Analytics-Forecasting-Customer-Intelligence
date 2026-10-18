-- Raw: external table over the immutable product category translation CSV
-- (Portuguese -> English) in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of
-- sql/staging/stg_category_translation.sql.
-- The source file starts with a UTF-8 BOM; skip_leading_rows = 1 skips the header
-- row, so the BOM never reaches a column name (the local read_csv does the same).
create or replace external table `${PROJECT}.raw.product_category_name_translation` (
    product_category_name          string,
    product_category_name_english  string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/product_category_name_translation.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);