-- mart_delivery_trend: port of sql/analytics/08_delivery_trend.sql (reports/analytics/08_delivery_trend.csv).
-- Grain: one row per purchase month (YYYY-MM) of labelled delivered orders (delivered, has an is_late label, no
-- timestamp anomaly: the same population as the late-delivery features). The promise columns show how far ahead the
-- estimated date was set; they changed sharply in 2018-08. Consumers must ORDER BY purchase_month.
--
-- Snowflake notes: strftime -> to_char; date_diff('second', a, b) -> datediff(second, a, b)::float / 86400.0.
select to_char(purchase_ts, 'YYYY-MM')                                                                         as purchase_month,
       count(*)                                                                                                as delivered_orders,
       round(100 * avg((case when is_late then 1 when not is_late then 0 end)::float), 1)                     as late_pct,
       round(median(delivery_days), 1)                                                                         as median_delivery_days,
       round(avg(datediff(second, purchase_ts, estimated_delivery_ts)::float / 86400.0), 1)                    as avg_promised_days,
       round(100 * avg((case when datediff(second, purchase_ts, estimated_delivery_ts)::float / 86400.0 < 20 then 1
                             when datediff(second, purchase_ts, estimated_delivery_ts)::float / 86400.0 >= 20 then 0 end)::float), 1) as promised_under_20d_pct
from {{ ref('fact_orders') }}
where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
group by 1
order by 1
