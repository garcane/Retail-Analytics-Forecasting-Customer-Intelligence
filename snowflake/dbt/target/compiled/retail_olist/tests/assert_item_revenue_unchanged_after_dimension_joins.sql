-- Singular test: returns the rows where expected and actual differ (a passing test returns zero rows).
-- Port of check 15 in sql/validation/checks.sql: item revenue unchanged after joining all dimensions (fan-out guard)
-- Expectations are derived from the staging models, never hard-coded EDA constants.
-- `is distinct from` makes a NULL expected/actual value fail instead of silently passing.
select expected, actual
from (
    select
        (select sum(price) from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items) as expected,
        (select sum(f.price)
         from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items f
         join RETAIL_OLIST.DBT_CI_MARTS.dim_customer  dc on dc.customer_key  = f.customer_key
         join RETAIL_OLIST.DBT_CI_MARTS.dim_product   dp on dp.product_key   = f.product_key
         join RETAIL_OLIST.DBT_CI_MARTS.dim_seller    ds on ds.seller_key    = f.seller_key
         join RETAIL_OLIST.DBT_CI_MARTS.dim_date      dd on dd.date_key      = f.purchase_date_key
         join RETAIL_OLIST.DBT_CI_MARTS.dim_geography gc on gc.geography_key = f.customer_geography_key
         join RETAIL_OLIST.DBT_CI_MARTS.dim_geography gs on gs.geography_key = f.seller_geography_key)   as actual
)
where expected is distinct from actual