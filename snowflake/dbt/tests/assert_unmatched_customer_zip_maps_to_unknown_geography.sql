-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 20 in sql/validation/checks.sql: orders whose customer zip is not in dim_geography map to unknown (-1) (anti-join form: also counts NULL zips, which the original NOT IN skipped)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(*)
         from {{ ref('stg_olist__orders') }} o
         join {{ ref('stg_olist__customers') }} c on c.customer_id = o.customer_id
         left join {{ ref('dim_geography') }} g
             on g.zip_prefix = c.customer_zip_code_prefix and g.geography_key <> -1
         where g.geography_key is null) as expected,
        (select count(*) from {{ ref('fact_orders') }} where customer_geography_key = -1)   as actual
)
where expected is distinct from actual
