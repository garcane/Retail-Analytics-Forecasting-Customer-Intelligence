-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 7 in sql/validation/checks.sql: dim_seller rows = stg_sellers rows (excluding -1)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from {{ ref('stg_olist__sellers') }}) as expected,
        (select count(*) from {{ ref('dim_seller') }} where seller_key <> -1)   as actual
)
where expected is distinct from actual
