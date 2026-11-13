-- Calibration of the published scores: within each month, five equal-size risk groups (0 = lowest), mean predicted
-- risk against the observed late rate. Same grouping as late_delivery_baseline.calibration_table: pandas
-- qcut(rank(method="first"), 5) over the month's rows in (purchase_ts, order_id) order, i.e. group b holds the ranks r
-- with r <= 1 + (n - 1) * (b + 1) / 5.
with ranked as (
    select
        month,
        risk_score,
        is_late,
        row_number() over (partition by month order by risk_score, purchase_ts, order_id) as r,
        count(*) over (partition by month) as n
    from {{ ref('mon_scores_latest_run') }}
)
select
    month,
    greatest(ceil((r - 1) * 5.0 / nullif(n - 1, 0)) - 1, 0)::int as risk_group,
    count(*) as orders,
    avg(risk_score) as predicted_late_rate,
    avg(is_late::float) as actual_late_rate
from ranked
group by 1, 2
