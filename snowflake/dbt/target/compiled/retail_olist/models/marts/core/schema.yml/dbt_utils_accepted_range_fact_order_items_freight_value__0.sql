

with meet_condition as(
  select *
  from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items
),

validation_errors as (
  select *
  from meet_condition
  where
    -- never true, defaults to an empty result set. Exists to ensure any combo of the `or` clauses below succeeds
    1 = 2
    -- records with a value >= min_value are permitted. The `not` flips this to find records that don't meet the rule.
    or not freight_value >= 0
)

select *
from validation_errors

