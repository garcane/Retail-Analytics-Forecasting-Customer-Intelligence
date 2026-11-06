-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 22 in sql/validation/checks.sql: dim_date contains all 30 days of 2016-11 (a month with no orders; a calendar fact, not an EDA constant)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select 30) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.dim_date where year_month = '2016-11')   as actual
)
where expected is distinct from actual