-- Month by month: what the model predicted against what happened, how much was flagged, and the delivery promise, whose
-- sharp shortening in 2018 (orders promised under 20 days) is what broke the model in August 2018.
select
    month,
    count(*) as orders,
    avg(risk_score) as mean_predicted_late_rate,
    avg(is_late::float) as actual_late_rate,
    avg(risk_score) - avg(is_late::float) as level_error,
    avg(iff(flagged_top10, 1.0, 0.0)::float) as share_flagged,
    avg(iff(flagged_top10, is_late::float, null)) as late_rate_flagged,
    median(promised_days) as median_promised_days,
    avg(iff(promised_days < 20, 1.0, 0.0)::float) as share_promised_under_20_days
from {{ ref('mon_scores_latest_run') }}
group by 1
