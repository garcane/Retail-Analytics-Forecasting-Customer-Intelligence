-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 3 in sql/validation/checks.sql: fact_payments rows = stg_order_payments rows
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_payments) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.fact_payments)   as actual
)
where expected is distinct from actual