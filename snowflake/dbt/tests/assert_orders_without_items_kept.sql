-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 16 in sql/validation/checks.sql: orders without items are kept in fact_orders (EDA: 775, derived from staging here)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*) from {{ ref('stg_olist__orders') }} where order_id not in (select order_id from {{ ref('stg_olist__order_items') }})) as expected,
        (select count(*) from {{ ref('fact_orders') }} where item_count = 0)   as actual
)
where expected is distinct from actual
