-- The latest published run of ML.LATE_DELIVERY_SCORES, joined to the feature mart for the purchase time (the order the
-- Python code ranks ties in) and the delivery promise the drift view looks at.
with latest as (
    select max(run_id) as run_id from {{ source('ml', 'late_delivery_scores') }}
)
select
    s.run_id,
    s.month,
    s.order_id,
    s.risk_score,
    s.risk_percentile,
    s.flagged_top10,
    s.is_late,
    f.purchase_ts,
    f.promised_days
from {{ source('ml', 'late_delivery_scores') }} s
join latest l on s.run_id = l.run_id
join {{ ref('mart_late_delivery_features') }} f on f.order_id = s.order_id
