-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 12 in sql/validation/checks.sql: sum(payment_value) fact_payments = staging (exact)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(payment_value) from {{ ref('stg_olist__order_payments') }}) as expected,
        (select sum(payment_value) from {{ ref('fact_payments') }})   as actual
)
where expected is distinct from actual
