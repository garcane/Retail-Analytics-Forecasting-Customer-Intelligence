-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 8 in sql/validation/checks.sql: dim_geography rows = distinct in-bounds zip prefixes (excluding -1)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select count(distinct geolocation_zip_code_prefix) from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__geolocation where geolocation_lat between -34 and 6 and geolocation_lng between -74 and -28) as expected,
        (select count(*) from RETAIL_OLIST.DBT_CI_MARTS.dim_geography where geography_key <> -1)   as actual
)
where expected is distinct from actual