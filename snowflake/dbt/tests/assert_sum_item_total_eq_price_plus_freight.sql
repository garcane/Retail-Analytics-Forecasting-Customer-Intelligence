-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 11 in sql/validation/checks.sql: sum(item_total_value) = sum(price) + sum(freight_value)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(price) + sum(freight_value) from {{ ref('stg_olist__order_items') }}) as expected,
        (select sum(item_total_value) from {{ ref('fact_order_items') }})   as actual
)
where expected is distinct from actual
