-- fact_reviews: one row per review. Port of sql/facts/fact_reviews.sql.
-- Grain: one row per (review_id, order_id). review_id alone is not unique (789 ids span several orders),
-- and 547 orders have 2-3 reviews, so never join this to the item fact on order_id; aggregate it first
-- or filter to is_latest_review_for_order.
-- Comment text stays on the row as nullable degenerate columns (58.7% of messages are null).
--
-- is_latest_review_for_order: latest creation date, then latest answer timestamp, then review_id ascending.
-- Both DESC keys carry an explicit NULLS LAST (Snowflake sorts NULLs first under DESC; DuckDB sorts them
-- last), which matters because review_answer_timestamp can be NULL.
select
    r.review_id,
    r.order_id,
    cast(coalesce(dc.customer_key, -1) as bigint)    as customer_key,
    coalesce(to_char(r.review_creation_date, 'YYYYMMDD')::integer, -1)         as review_creation_date_key,
    coalesce(to_char(r.review_answer_timestamp, 'YYYYMMDD')::integer, -1)      as review_answer_date_key,
    r.review_creation_date                           as review_creation_ts,
    r.review_answer_timestamp                        as review_answer_ts,
    r.review_score,
    r.review_comment_title,
    r.review_comment_message,
    (r.review_comment_title is not null or r.review_comment_message is not null) as has_comment,
    (
        row_number() over (
            partition by r.order_id
            order by r.review_creation_date desc nulls last,
                     r.review_answer_timestamp desc nulls last,
                     r.review_id
        ) = 1
    )                                                as is_latest_review_for_order
from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_reviews r
join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__orders o
    on o.order_id = r.order_id
left join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__customers c
    on c.customer_id = o.customer_id
left join RETAIL_OLIST.DBT_CI_MARTS.dim_customer dc
    on dc.customer_unique_id = c.customer_unique_id