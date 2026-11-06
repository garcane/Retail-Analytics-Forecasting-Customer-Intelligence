-- Staging: typed view over RAW.ORDER_REVIEWS. Port of sql/staging/stg_order_reviews.sql.
-- Grain: one row per (review_id, order_id). review_id alone is NOT unique:
-- 789 review ids appear on more than one order, and 547 orders have 2-3 reviews.
-- Comment text is NOT trimmed: DuckDB keeps whitespace-padded messages as-is, so does this model.
select
    nullif(review_id, '')                                                              as review_id,
    nullif(order_id, '')                                                               as order_id,
    cast(nullif(review_score, '') as integer)                                          as review_score,
    nullif(review_comment_title, '')                                                   as review_comment_title,
    nullif(review_comment_message, '')                                                 as review_comment_message,
    to_timestamp_ntz(nullif(review_creation_date, ''), 'YYYY-MM-DD HH24:MI:SS')        as review_creation_date,
    to_timestamp_ntz(nullif(review_answer_timestamp, ''), 'YYYY-MM-DD HH24:MI:SS')     as review_answer_timestamp
from RETAIL_OLIST.RAW.order_reviews