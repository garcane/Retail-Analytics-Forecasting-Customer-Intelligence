{{ config(alias='fact_order_items') }}

-- pbi_fact_order_items: Power BI-facing view, schema PBI, object FACT_ORDER_ITEMS. Port of the `fact_order_items` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
-- is_net_order: not canceled or unavailable (sql/analytics/01, 02, 04). Unlike fact_orders it has no item_count test.
select
    order_id,
    order_item_id,
    order_status,
    customer_key,
    product_key,
    seller_key,
    customer_geography_key,
    seller_geography_key,
    purchase_date_key,
    shipping_limit_date_key,
    price,
    freight_value,
    item_total_value,
    (order_status not in ('canceled', 'unavailable')) as is_net_order
from {{ ref('fact_order_items') }}
