-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 14 in sql/validation/checks.sql: sum(payment_total) fact_orders = sum(payment_value) fact_payments
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(payment_value) from {{ ref('fact_payments') }}) as expected,
        (select sum(payment_total) from {{ ref('fact_orders') }})   as actual
)
where expected is distinct from actual
