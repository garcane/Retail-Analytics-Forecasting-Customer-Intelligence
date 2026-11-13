-- Calibration averaged over the test months, per risk group: the same figures as calibration_logistic_regression
-- (features v1) in reports/snowflake/late_delivery_metrics.json, which also averages the months.
select
    risk_group,
    avg(predicted_late_rate) as predicted_late_rate,
    avg(actual_late_rate) as actual_late_rate,
    count(*) as months
from {{ ref('mon_calibration_by_month') }}
group by 1
