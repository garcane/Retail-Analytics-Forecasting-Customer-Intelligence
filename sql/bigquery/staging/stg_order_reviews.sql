-- Staging: typed view over the raw order reviews file.
-- Grain: one row per (review_id, order_id). review_id alone is NOT unique:
-- 789 review ids appear on more than one order, and 547 orders have 2-3 reviews.
create or replace view `${PROJECT}.staging.stg_order_reviews` as
select
    review_id,
    order_id,
    cast(review_score            as int64)   as review_score,
    review_comment_title,
    review_comment_message,
    cast(review_creation_date    as datetime) as review_creation_date,
    cast(review_answer_timestamp as datetime) as review_answer_timestamp
from `${PROJECT}.raw.olist_order_reviews_dataset`;