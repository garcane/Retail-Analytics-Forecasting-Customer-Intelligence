-- Delivery performance and the delivery promise by purchase month (delivered orders). The promise columns show how
-- far ahead the estimated date was set; they changed sharply in 2018-08 (docs/ml/DRIFT_ANALYSIS.md).
select strftime(purchase_ts, '%Y-%m')                                                               as purchase_month,
       count(*)                                                                                      as delivered_orders,
       round(100 * avg(is_late::integer), 1)                                                         as late_pct,
       round(median(delivery_days), 1)                                                               as median_delivery_days,
       round(avg(date_diff('second', purchase_ts, estimated_delivery_ts) / 86400.0), 1)              as avg_promised_days,
       round(100 * avg((date_diff('second', purchase_ts, estimated_delivery_ts) / 86400.0 < 20)::integer), 1) as promised_under_20d_pct
from fact_orders
where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
group by 1
order by 1;
