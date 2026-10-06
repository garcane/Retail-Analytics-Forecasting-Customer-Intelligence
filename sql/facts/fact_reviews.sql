-- fact_reviews: one row per review.
-- Grain: one row per (review_id, order_id). review_id alone is not unique (789 ids span several orders),
-- and 547 orders have 2-3 reviews, so never join this to the item fact on order_id; aggregate it first
-- or filter to is_latest_review_for_order.
-- Comment text stays on the row as nullable degenerate columns (58.7% of messages are null).
create table fact_reviews (
    review_id                     VARCHAR NOT NULL,   -- degenerate
    order_id                      VARCHAR NOT NULL,   -- degenerate
    customer_key                  BIGINT  NOT NULL REFERENCES dim_customer (customer_key),
    review_creation_date_key      INTEGER NOT NULL REFERENCES dim_date (date_key),
    review_answer_date_key        INTEGER NOT NULL REFERENCES dim_date (date_key),
    review_creation_ts            TIMESTAMP,
    review_answer_ts              TIMESTAMP,
    review_score                  INTEGER NOT NULL,   -- 1 (worst) to 5 (best)
    review_comment_title          VARCHAR,
    review_comment_message        VARCHAR,
    has_comment                   BOOLEAN NOT NULL,   -- title or message present
    is_latest_review_for_order    BOOLEAN NOT NULL,
    PRIMARY KEY (review_id, order_id)
);

insert into fact_reviews
select
    r.review_id,
    r.order_id,
    coalesce(dc.customer_key, -1),
    coalesce(strftime(r.review_creation_date,    '%Y%m%d')::integer, -1),
    coalesce(strftime(r.review_answer_timestamp, '%Y%m%d')::integer, -1),
    r.review_creation_date,
    r.review_answer_timestamp,
    r.review_score,
    r.review_comment_title,
    r.review_comment_message,
    r.review_comment_title is not null or r.review_comment_message is not null,
    row_number() over (
        partition by r.order_id
        order by r.review_creation_date desc, r.review_answer_timestamp desc, r.review_id
    ) = 1
from stg_order_reviews r
join stg_orders o         on o.order_id = r.order_id
left join stg_customers c on c.customer_id = o.customer_id
left join dim_customer dc on dc.customer_unique_id = c.customer_unique_id;
