-- Raw: external table over the immutable customers CSV in Cloud Storage
-- (gs://<bucket>/raw/olist/olist_customers_dataset.csv; the RAW layer, never modified).
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_customers.sql.
-- Every column is read as STRING so the bytes are kept as written -- zip prefixes
-- keep their leading zeros -- and the typed model lives in the staging view.
-- The header row is skipped, so the schema maps to the columns positionally.
create or replace external table `${PROJECT}.raw.olist_customers_dataset` (
    customer_id              string,
    customer_unique_id       string,
    customer_zip_code_prefix string,  -- STRING so '01046' keeps its leading zero
    customer_city            string,
    customer_state           string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_customers_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);