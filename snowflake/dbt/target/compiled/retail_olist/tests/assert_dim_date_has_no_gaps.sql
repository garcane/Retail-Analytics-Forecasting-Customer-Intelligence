-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 21 in sql/validation/checks.sql: dim_date has no gaps
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select datediff(day, min(full_date), max(full_date)) + 1 from RETAIL_OLIST.DBT_CI_MARTS.dim_date where date_key <> -1) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.dim_date where date_key <> -1)   as actual
)
where expected is distinct from actual