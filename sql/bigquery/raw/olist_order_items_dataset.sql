-- Raw: external table over the immutable order items CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_order_items.sql.
-- Money columns stay STRING here; staging.stg_order_items casts them to NUMERIC
-- (DECIMAL(12,2) -> NUMERIC) so sums are exact.
create or replace external table `${PROJECT}.raw.olist_order_items_dataset` (
    order_id            string,
    order_item_id       string,
    product_id          string,
    seller_id           string,
    shipping_limit_date string,
    price               string,
    freight_value       string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_order_items_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);