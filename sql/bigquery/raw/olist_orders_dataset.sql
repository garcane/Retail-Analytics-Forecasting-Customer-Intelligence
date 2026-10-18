-- Raw: external table over the immutable orders CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_orders.sql.
-- The five timestamp columns stay STRING here; staging.stg_orders casts them to
-- DATETIME (TIMESTAMP without a time zone -> DATETIME).
create or replace external table `${PROJECT}.raw.olist_orders_dataset` (
    order_id                      string,
    customer_id                   string,
    order_status                  string,
    order_purchase_timestamp      string,  -- DATETIME in staging.stg_orders
    order_approved_at             string,  -- DATETIME in staging.stg_orders
    order_delivered_carrier_date  string,  -- DATETIME in staging.stg_orders
    order_delivered_customer_date string,  -- DATETIME in staging.stg_orders
    order_estimated_delivery_date string   -- DATETIME in staging.stg_orders
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_orders_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);