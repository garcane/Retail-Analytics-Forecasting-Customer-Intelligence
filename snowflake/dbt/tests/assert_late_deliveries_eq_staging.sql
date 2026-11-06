-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 17 in sql/validation/checks.sql: late deliveries in fact_orders = delivered-after-estimate orders in staging (EDA: 7827 is a reconciliation output, not a threshold here)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from {{ ref('stg_olist__orders') }} where order_delivered_customer_date > order_estimated_delivery_date) as expected,
        (select count(*) from {{ ref('fact_orders') }} where is_late)   as actual
)
where expected is distinct from actual
