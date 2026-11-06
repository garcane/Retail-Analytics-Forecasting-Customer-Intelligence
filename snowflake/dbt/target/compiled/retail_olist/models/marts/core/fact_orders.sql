-- fact_orders: one row per order, including the orders that have no items. Port of sql/facts/fact_orders.sql.
-- Grain: one row per order_id. Order-level process measures: lifecycle dates, delivery time, lateness.
-- Items and payments are pre-aggregated to the order grain BEFORE joining (int_order_items_agg,
-- int_order_payments_agg): joining them side by side would repeat rows and overstate item revenue by ~4.5-5%.
-- Missing milestone dates map to date_key -1 (not applicable); the raw timestamps stay nullable.
--
-- Snowflake notes
--   * date_diff('second', a, b) / 86400.0  ->  datediff(second, a, b)::float / 86400.0  (float, not NUMBER scale)
--   * sums are cast back to number(12,2) because Snowflake widens SUM() to NUMBER(38,2)
select
    o.order_id,
    o.customer_id,
    o.order_status,
    cast(coalesce(dc.customer_key, -1) as bigint)               as customer_key,
    cast(coalesce(g.geography_key, -1) as bigint)               as customer_geography_key,
    coalesce(to_char(o.order_purchase_timestamp, 'YYYYMMDD')::integer, -1)                as purchase_date_key,
    coalesce(to_char(o.order_approved_at, 'YYYYMMDD')::integer, -1)                        as approved_date_key,
    coalesce(to_char(o.order_delivered_carrier_date, 'YYYYMMDD')::integer, -1)            as carrier_date_key,
    coalesce(to_char(o.order_delivered_customer_date, 'YYYYMMDD')::integer, -1)           as delivered_customer_date_key,
    coalesce(to_char(o.order_estimated_delivery_date, 'YYYYMMDD')::integer, -1)           as estimated_delivery_date_key,
    o.order_purchase_timestamp                                  as purchase_ts,
    o.order_approved_at                                         as approved_ts,
    o.order_delivered_carrier_date                              as carrier_ts,
    o.order_delivered_customer_date                             as delivered_customer_ts,
    o.order_estimated_delivery_date                             as estimated_delivery_ts,
    cast(coalesce(i.item_count, 0) as integer)                  as item_count,           -- 0 for orders with no items
    cast(coalesce(i.items_price, 0) as number(12, 2))           as items_price,
    cast(coalesce(i.items_freight, 0) as number(12, 2))         as items_freight,
    cast(coalesce(p.payment_count, 0) as integer)               as payment_count,
    cast(coalesce(p.payment_total, 0) as number(12, 2))         as payment_total,
    -- purchase -> customer delivery, fractional days
    datediff(second, o.order_purchase_timestamp, o.order_delivered_customer_date)::float / 86400.0
                                                                as delivery_days,
    -- delivered - estimated; positive = late
    datediff(second, o.order_estimated_delivery_date, o.order_delivered_customer_date)::float / 86400.0
                                                                as delivery_delay_days,
    -- delivered after the estimate; NULL if no delivery date
    o.order_delivered_customer_date > o.order_estimated_delivery_date
                                                                as is_late,
    -- carrier before purchase, or customer before carrier
    (
        coalesce(o.order_delivered_carrier_date < o.order_purchase_timestamp, false)
        or coalesce(o.order_delivered_customer_date < o.order_delivered_carrier_date, false)
    )                                                           as has_timestamp_anomaly
from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__orders o
left join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__customers c
    on c.customer_id = o.customer_id
left join RETAIL_OLIST.DBT_CI_MARTS.dim_customer dc
    on dc.customer_unique_id = c.customer_unique_id
left join RETAIL_OLIST.DBT_CI_MARTS.dim_geography g
    on g.zip_prefix = c.customer_zip_code_prefix
left join RETAIL_OLIST.DBT_CI_INTERMEDIATE.int_order_items_agg i
    on i.order_id = o.order_id
left join RETAIL_OLIST.DBT_CI_INTERMEDIATE.int_order_payments_agg p
    on p.order_id = o.order_id