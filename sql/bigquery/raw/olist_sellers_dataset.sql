-- Raw: external table over the immutable sellers CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_sellers.sql.
-- The zip prefix stays STRING so leading zeros survive.
create or replace external table `${PROJECT}.raw.olist_sellers_dataset` (
    seller_id              string,
    seller_zip_code_prefix string,  -- STRING so '13023'-style prefixes keep leading zeros
    seller_city            string,
    seller_state           string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_sellers_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);