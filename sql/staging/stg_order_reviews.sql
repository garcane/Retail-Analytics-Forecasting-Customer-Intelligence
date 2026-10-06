-- Staging: typed view over the raw order reviews file.
-- Grain: one row per (review_id, order_id). review_id alone is NOT unique:
-- 789 review ids appear on more than one order, and 547 orders have 2-3 reviews.
create or replace view stg_order_reviews as
select *
from read_csv(
    '${DATA_DIR}/olist_order_reviews_dataset.csv',
    header = true,
    columns = {
        'review_id': 'VARCHAR',
        'order_id': 'VARCHAR',
        'review_score': 'INTEGER',
        'review_comment_title': 'VARCHAR',
        'review_comment_message': 'VARCHAR',
        'review_creation_date': 'TIMESTAMP',
        'review_answer_timestamp': 'TIMESTAMP'
    }
);
