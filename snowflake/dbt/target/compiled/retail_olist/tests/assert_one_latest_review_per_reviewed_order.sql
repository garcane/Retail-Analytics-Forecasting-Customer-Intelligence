-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 19 in sql/validation/checks.sql: one latest review per reviewed order
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(distinct order_id) from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_reviews) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.fact_reviews where is_latest_review_for_order)   as actual
)
where expected is distinct from actual