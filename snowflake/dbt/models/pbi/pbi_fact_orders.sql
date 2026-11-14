{{ config(alias='fact_orders') }}

-- pbi_fact_orders: Power BI-facing view, schema PBI, object FACT_ORDERS. Port of the `fact_orders` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
-- Derived columns (kept in SQL so the DAX stays short and ties to the definitions used everywhere else):
--   promised_days         the promise shown at checkout, in days
--   is_net_order          not canceled or unavailable, and has items: sql/analytics/01, 03, 07
--   is_labelled_delivery  delivered, has a late/on-time label, no timestamp anomaly: the ML-feature population
--   delay_bucket(_order)  delivered orders only; same buckets as sql/analytics/05_delivery_vs_reviews.sql
-- Only purchase_ts and estimated_delivery_ts are exported as timestamps; customer_id and the other *_ts columns are not.
select
    order_id,
    order_status,
    customer_key,
    customer_geography_key,
    purchase_date_key,
    approved_date_key,
    carrier_date_key,
    delivered_customer_date_key,
    estimated_delivery_date_key,
    purchase_ts,
    estimated_delivery_ts,
    item_count,
    items_price,
    items_freight,
    payment_count,
    payment_total,
    delivery_days,
    delivery_delay_days,
    is_late,
    has_timestamp_anomaly,
    datediff(second, purchase_ts, estimated_delivery_ts)::float / 86400.0 as promised_days,
    (order_status not in ('canceled', 'unavailable') and item_count > 0) as is_net_order,
    (order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly) as is_labelled_delivery,
    case when order_status <> 'delivered' or delivery_delay_days is null then null
         when delivery_delay_days <= 0  then 'on time or early'
         when delivery_delay_days <= 3  then '1-3 days late'
         when delivery_delay_days <= 7  then '4-7 days late'
         when delivery_delay_days <= 14 then '8-14 days late'
         else 'more than 14 days late' end as delay_bucket,
    case when order_status <> 'delivered' or delivery_delay_days is null then null
         when delivery_delay_days <= 0  then 1 when delivery_delay_days <= 3 then 2
         when delivery_delay_days <= 7  then 3 when delivery_delay_days <= 14 then 4 else 5 end::integer as delay_bucket_order
from {{ ref('fact_orders') }}
