-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 6 in sql/validation/checks.sql: dim_product rows = stg_products rows (excluding -1)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__products) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.dim_product where product_key <> -1)   as actual
)
where expected is distinct from actual