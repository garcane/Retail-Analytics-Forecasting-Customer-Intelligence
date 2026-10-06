-- Validation: reconcile the star schema against staging (the raw data) and against the EDA findings.
-- Returns one row per check; the build fails if any `passed` is false.
-- Primary-key uniqueness and foreign-key coverage are enforced by the table constraints themselves.
with checks(check_name, expected, actual) as (

    -- row counts: facts keep every source row
    select 'fact_orders rows = stg_orders rows',
           (select count(*) from stg_orders)::varchar, (select count(*) from fact_orders)::varchar
    union all select 'fact_order_items rows = stg_order_items rows',
           (select count(*) from stg_order_items)::varchar, (select count(*) from fact_order_items)::varchar
    union all select 'fact_payments rows = stg_order_payments rows',
           (select count(*) from stg_order_payments)::varchar, (select count(*) from fact_payments)::varchar
    union all select 'fact_reviews rows = stg_order_reviews rows',
           (select count(*) from stg_order_reviews)::varchar, (select count(*) from fact_reviews)::varchar

    -- row counts: dimensions (excluding the -1 unknown member)
    union all select 'dim_customer rows = distinct customer_unique_id',
           (select count(distinct customer_unique_id) from stg_customers)::varchar,
           (select count(*) from dim_customer where customer_key <> -1)::varchar
    union all select 'dim_product rows = stg_products rows',
           (select count(*) from stg_products)::varchar, (select count(*) from dim_product where product_key <> -1)::varchar
    union all select 'dim_seller rows = stg_sellers rows',
           (select count(*) from stg_sellers)::varchar, (select count(*) from dim_seller where seller_key <> -1)::varchar
    union all select 'dim_geography rows = distinct in-bounds zip prefixes',
           (select count(distinct geolocation_zip_code_prefix) from stg_geolocation
            where geolocation_lat between -34 and 6 and geolocation_lng between -74 and -28)::varchar,
           (select count(*) from dim_geography where geography_key <> -1)::varchar

    -- money reconciles exactly
    union all select 'sum(price) fact_order_items = staging',
           (select sum(price) from stg_order_items)::varchar, (select sum(price) from fact_order_items)::varchar
    union all select 'sum(freight_value) fact_order_items = staging',
           (select sum(freight_value) from stg_order_items)::varchar, (select sum(freight_value) from fact_order_items)::varchar
    union all select 'sum(item_total_value) = sum(price) + sum(freight_value)',
           (select sum(price) + sum(freight_value) from stg_order_items)::varchar,
           (select sum(item_total_value) from fact_order_items)::varchar
    union all select 'sum(payment_value) fact_payments = staging',
           (select sum(payment_value) from stg_order_payments)::varchar, (select sum(payment_value) from fact_payments)::varchar
    union all select 'sum(items_price) fact_orders = sum(price) fact_order_items',
           (select sum(price) from fact_order_items)::varchar, (select sum(items_price) from fact_orders)::varchar
    union all select 'sum(payment_total) fact_orders = sum(payment_value) fact_payments',
           (select sum(payment_value) from fact_payments)::varchar, (select sum(payment_total) from fact_orders)::varchar

    -- fan-out: joining the item fact to every dimension (one-to-one) must not change revenue
    union all select 'item revenue unchanged after joining all dimensions',
           (select sum(price) from fact_order_items)::varchar,
           (select sum(f.price)
            from fact_order_items f
            join dim_customer  dc on dc.customer_key  = f.customer_key
            join dim_product   dp on dp.product_key   = f.product_key
            join dim_seller    ds on ds.seller_key    = f.seller_key
            join dim_date      dd on dd.date_key      = f.purchase_date_key
            join dim_geography gc on gc.geography_key = f.customer_geography_key
            join dim_geography gs on gs.geography_key = f.seller_geography_key)::varchar

    -- EDA findings still hold in the model
    union all select 'orders without items kept in fact_orders (EDA: 775)',
           (select count(*) from stg_orders where order_id not in (select order_id from stg_order_items))::varchar,
           (select count(*) from fact_orders where item_count = 0)::varchar
    union all select 'late deliveries (EDA: 7827)', '7827', (select count(*) from fact_orders where is_late)::varchar
    union all select 'timestamp anomaly orders flagged (EDA: 166 carrier-before-purchase, 23 customer-before-carrier, 2 overlap or fewer)',
           'true',
           ((select count(*) from fact_orders where has_timestamp_anomaly)
            between 166 and 166 + 23)::varchar
    union all select 'one latest review per reviewed order',
           (select count(distinct order_id) from stg_order_reviews)::varchar,
           (select count(*) from fact_reviews where is_latest_review_for_order)::varchar
    union all select 'orders whose customer zip is not in dim_geography map to unknown (-1)',
           (select count(*) from stg_orders o join stg_customers c using (customer_id)
            where c.customer_zip_code_prefix not in (select zip_prefix from dim_geography where zip_prefix is not null))::varchar,
           (select count(*) from fact_orders where customer_geography_key = -1)::varchar

    -- calendar is complete: no gaps, including months with no orders (2016-11)
    union all select 'dim_date has no gaps',
           (select (max(full_date) - min(full_date) + 1)::varchar from dim_date where date_key <> -1),
           (select count(*)::varchar from dim_date where date_key <> -1)
    union all select 'dim_date contains all 30 days of 2016-11 (a month with no orders)',
           '30', (select count(*)::varchar from dim_date where year_month = '2016-11')
)
select check_name, expected, actual, expected = actual as passed
from checks;
