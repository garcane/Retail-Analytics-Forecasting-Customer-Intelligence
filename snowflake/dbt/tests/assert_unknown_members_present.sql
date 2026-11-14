-- Singular test: every dimension carries exactly one -1 unknown member (the facts map unmatched lookups to it).
-- Returns the dimensions that do not have exactly one.
select dim_name, n_unknown
from (
    select 'dim_customer' as dim_name, count(*) as n_unknown from {{ ref('dim_customer') }} where customer_key = -1
    union all select 'dim_product',    count(*) from {{ ref('dim_product') }}   where product_key = -1
    union all select 'dim_seller',     count(*) from {{ ref('dim_seller') }}    where seller_key = -1
    union all select 'dim_geography',  count(*) from {{ ref('dim_geography') }} where geography_key = -1
    union all select 'dim_date',       count(*) from {{ ref('dim_date') }}      where date_key = -1
)
where n_unknown <> 1
