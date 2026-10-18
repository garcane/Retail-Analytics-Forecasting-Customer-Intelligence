-- Raw: external table over the immutable order payments CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_order_payments.sql.
-- payment_value stays STRING here; staging.stg_order_payments casts it to NUMERIC.
create or replace external table `${PROJECT}.raw.olist_order_payments_dataset` (
    order_id             string,
    payment_sequential   string,
    payment_type         string,
    payment_installments string,
    payment_value        string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_order_payments_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);