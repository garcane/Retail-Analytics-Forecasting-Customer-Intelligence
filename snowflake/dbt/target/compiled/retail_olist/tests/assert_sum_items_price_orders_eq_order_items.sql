-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 13 in sql/validation/checks.sql: sum(items_price) fact_orders = sum(price) fact_order_items
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(price) from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items) as expected,
        (select sum(items_price) from RETAIL_OLIST.DBT_CI_MARTS.fact_orders)   as actual
)
where expected is distinct from actual