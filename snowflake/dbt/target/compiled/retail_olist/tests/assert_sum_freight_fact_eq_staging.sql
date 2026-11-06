-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 10 in sql/validation/checks.sql: sum(freight_value) fact_order_items = staging (exact)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(freight_value) from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_items) as expected,
        (select sum(freight_value) from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items)   as actual
)
where expected is distinct from actual