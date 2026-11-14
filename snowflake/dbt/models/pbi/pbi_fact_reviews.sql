{{ config(alias='fact_reviews') }}

-- pbi_fact_reviews: Power BI-facing view, schema PBI, object FACT_REVIEWS. Port of the `fact_reviews` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
-- review_comment_title / review_comment_message are deliberately NOT exposed: no analysis uses them and they are
-- free text written by customers.
select
    review_id,
    order_id,
    customer_key,
    review_creation_date_key,
    review_answer_date_key,
    review_creation_ts,
    review_answer_ts,
    review_score,
    has_comment,
    is_latest_review_for_order
from {{ ref('fact_reviews') }}
