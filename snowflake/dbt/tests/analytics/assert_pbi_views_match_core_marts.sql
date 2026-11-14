-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of src/powerbi/export_data.py (row counts and key totals of the PBI views). Expectations are derived from the fact tables, never hard-coded.
-- Row-count parity with the core marts (pbi_dim_date drops only the -1 row) and the headline totals the report uses.
with c as (
    select 'dim_date' as t, (select count(*) from {{ ref('dim_date') }}) - 1 as expected, (select count(*) from {{ ref('pbi_dim_date') }}) as actual
    union all select 'dim_customer', (select count(*) from {{ ref('dim_customer') }}), (select count(*) from {{ ref('pbi_dim_customer') }})
    union all select 'dim_product', (select count(*) from {{ ref('dim_product') }}), (select count(*) from {{ ref('pbi_dim_product') }})
    union all select 'dim_seller', (select count(*) from {{ ref('dim_seller') }}), (select count(*) from {{ ref('pbi_dim_seller') }})
    union all select 'dim_geography', (select count(*) from {{ ref('dim_geography') }}), (select count(*) from {{ ref('pbi_dim_geography') }})
    union all select 'fact_orders', (select count(*) from {{ ref('fact_orders') }}), (select count(*) from {{ ref('pbi_fact_orders') }})
    union all select 'fact_order_items', (select count(*) from {{ ref('fact_order_items') }}), (select count(*) from {{ ref('pbi_fact_order_items') }})
    union all select 'fact_payments', (select count(*) from {{ ref('fact_payments') }}), (select count(*) from {{ ref('pbi_fact_payments') }})
    union all select 'fact_reviews', (select count(*) from {{ ref('fact_reviews') }}), (select count(*) from {{ ref('pbi_fact_reviews') }})
    union all select 'net orders (pbi_fact_orders.is_net_order = mart_state_performance.orders)',
        (select sum(orders) from {{ ref('mart_state_performance') }}),
        (select count(*) from {{ ref('pbi_fact_orders') }} where is_net_order)
    union all select 'labelled deliveries (pbi_fact_orders.is_labelled_delivery = mart_delivery_trend.delivered_orders)',
        (select sum(delivered_orders) from {{ ref('mart_delivery_trend') }}),
        (select count(*) from {{ ref('pbi_fact_orders') }} where is_labelled_delivery)
    union all select 'net items (pbi_fact_order_items.is_net_order = mart_monthly_kpis.items)',
        (select sum(items) from {{ ref('mart_monthly_kpis') }}),
        (select count(*) from {{ ref('pbi_fact_order_items') }} where is_net_order)
    union all select 'delivered orders with a delay have a bucket',
        (select count(*) from {{ ref('fact_orders') }} where order_status = 'delivered' and delivery_delay_days is not null),
        (select count(*) from {{ ref('pbi_fact_orders') }} where delay_bucket is not null and delay_bucket_order is not null)
)
select t as failed_check, expected, actual from c where expected is distinct from actual
