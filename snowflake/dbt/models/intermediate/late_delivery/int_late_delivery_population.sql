-- int_late_delivery_population: the orders the late-delivery model is trained and scored on.
-- Port of the `pop` CTE of sql/ml/late_delivery_features.sql (D-007).
-- Grain: one row per order_id. Prediction point = purchase_ts.
--
-- Population filter (identical to DuckDB): delivered orders that have a label (is_late is not null) and no
-- timestamp anomaly. The columns kept are only those the feature query needs; order_status and
-- has_timestamp_anomaly are used as row filters and deliberately NOT carried forward (leakage rules,
-- docs/ml/LEAKAGE_ANALYSIS.md). delivered_customer_ts is kept only so that the history models can order
-- outcomes in time and so the training code can drop rows whose outcome was unknown at the start of a test
-- period. It is never a feature.
select
    order_id,
    customer_key,
    customer_geography_key,
    purchase_ts,
    estimated_delivery_ts,
    delivered_customer_ts,
    is_late,
    item_count,
    items_price,
    items_freight,
    payment_count
from {{ ref('fact_orders') }}
where order_status = 'delivered'
  and is_late is not null
  and not has_timestamp_anomaly
