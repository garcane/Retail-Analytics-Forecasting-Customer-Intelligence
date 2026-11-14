-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 18 in sql/validation/checks.sql: timestamp-anomaly orders flagged = carrier-before-purchase OR customer-before-carrier in staging (EDA: 166 / 23 / overlap are reconciliation outputs, not thresholds here)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from {{ ref('stg_olist__orders') }}
         where coalesce(order_delivered_carrier_date < order_purchase_timestamp, false)
            or coalesce(order_delivered_customer_date < order_delivered_carrier_date, false)) as expected,
        (select count(*) from {{ ref('fact_orders') }} where has_timestamp_anomaly)   as actual
)
where expected is distinct from actual
