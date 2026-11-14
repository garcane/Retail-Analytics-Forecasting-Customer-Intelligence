-- ddl_raw.sql  --  RAW layer tables (idempotent: CREATE TABLE IF NOT EXISTS only).
--
-- Every source column is VARCHAR and keeps the CSV header name (unquoted, so Snowflake stores it
-- upper-case). Source typos are preserved on purpose (product_name_lenght, product_description_lenght).
-- Typing, renaming and cleaning happen in dbt staging, never here.
-- Each table also carries four load-metadata columns filled by ingestion/load_raw.py:
--   _loaded_at           load timestamp (CURRENT_TIMESTAMP at COPY time)
--   _source_file         METADATA$FILENAME of the staged file
--   _source_row_number   METADATA$FILE_ROW_NUMBER -- informational only (not guaranteed to equal the
--                        record number for records containing embedded newlines; UNVERIFIED)
--   _batch_id            id of the load_raw.py run that loaded the row
--
-- Run as RETAIL_LOADER (so the loader owns the tables) AFTER 01_objects.sql / 02_grants.sql.
-- Re-running never alters or removes existing tables or data.
--
-- STATUS: written offline; NOT RUN against any Snowflake account (UNVERIFIED).
-- load_raw.py column lists are checked against this file by tests/test_snowflake_ingestion.py.

USE ROLE RETAIL_LOADER;
USE WAREHOUSE RETAIL_WH;
USE SCHEMA RETAIL_OLIST.RAW;

CREATE TABLE IF NOT EXISTS RAW.CUSTOMERS (
    customer_id                    VARCHAR,
    customer_unique_id             VARCHAR,
    customer_zip_code_prefix       VARCHAR,
    customer_city                  VARCHAR,
    customer_state                 VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_customers_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.GEOLOCATION (
    geolocation_zip_code_prefix    VARCHAR,
    geolocation_lat                VARCHAR,
    geolocation_lng                VARCHAR,
    geolocation_city               VARCHAR,
    geolocation_state              VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_geolocation_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.ORDER_ITEMS (
    order_id                       VARCHAR,
    order_item_id                  VARCHAR,
    product_id                     VARCHAR,
    seller_id                      VARCHAR,
    shipping_limit_date            VARCHAR,
    price                          VARCHAR,
    freight_value                  VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_order_items_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.ORDER_PAYMENTS (
    order_id                       VARCHAR,
    payment_sequential             VARCHAR,
    payment_type                   VARCHAR,
    payment_installments           VARCHAR,
    payment_value                  VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_order_payments_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.ORDER_REVIEWS (
    review_id                      VARCHAR,
    order_id                       VARCHAR,
    review_score                   VARCHAR,
    review_comment_title           VARCHAR,
    review_comment_message         VARCHAR,
    review_creation_date           VARCHAR,
    review_answer_timestamp        VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_order_reviews_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.ORDERS (
    order_id                       VARCHAR,
    customer_id                    VARCHAR,
    order_status                   VARCHAR,
    order_purchase_timestamp       VARCHAR,
    order_approved_at              VARCHAR,
    order_delivered_carrier_date   VARCHAR,
    order_delivered_customer_date  VARCHAR,
    order_estimated_delivery_date  VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_orders_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.PRODUCTS (
    product_id                     VARCHAR,
    product_category_name          VARCHAR,
    product_name_lenght            VARCHAR,
    product_description_lenght     VARCHAR,
    product_photos_qty             VARCHAR,
    product_weight_g               VARCHAR,
    product_length_cm              VARCHAR,
    product_height_cm              VARCHAR,
    product_width_cm               VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_products_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.SELLERS (
    seller_id                      VARCHAR,
    seller_zip_code_prefix         VARCHAR,
    seller_city                    VARCHAR,
    seller_state                   VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of olist_sellers_dataset.csv';

CREATE TABLE IF NOT EXISTS RAW.PRODUCT_CATEGORY_TRANSLATION (
    product_category_name          VARCHAR,
    product_category_name_english  VARCHAR,
    _loaded_at                     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _source_file                   VARCHAR,
    _source_row_number             NUMBER(38,0),
    _batch_id                      VARCHAR
) COMMENT = 'Verbatim load of product_category_name_translation.csv';

-- One row per file load attempt. A file (sha256) with a SUCCESS row is skipped on re-run.
CREATE TABLE IF NOT EXISTS RAW.INGESTION_LOG (
    batch_id       VARCHAR,
    table_name     VARCHAR,
    file_name      VARCHAR,
    sha256         VARCHAR,
    expected_rows  NUMBER(38,0),
    loaded_rows    NUMBER(38,0),
    loaded_at      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    status         VARCHAR       -- SUCCESS | FAILED
) COMMENT = 'Audit log written by ingestion/load_raw.py';
