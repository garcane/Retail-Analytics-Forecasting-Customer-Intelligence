-- Raw: external table over the immutable order reviews CSV in Cloud Storage.
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_order_reviews.sql.
-- allow_quoted_newlines is required here: 3,852 review comments contain line breaks
-- inside quotes (DuckDB's reader accepts them by default; BigQuery's does not unless told).
create or replace external table `${PROJECT}.raw.olist_order_reviews_dataset` (
    review_id               string,
    order_id                string,
    review_score            string,
    review_comment_title    string,  -- empty in 87,656 rows; NULL in both readers
    review_comment_message  string,
    review_creation_date    string,  -- DATETIME in staging.stg_order_reviews
    review_answer_timestamp string   -- DATETIME in staging.stg_order_reviews
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_order_reviews_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true
);