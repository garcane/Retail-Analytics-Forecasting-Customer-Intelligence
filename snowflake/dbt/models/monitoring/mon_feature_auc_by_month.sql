-- Single-feature skill by purchase month: the ROC-AUC of one raw feature as a ranking of that month's late orders
-- (0.5 = no skill, below 0.5 = pointing the wrong way). Mirrors E1 of src/ml/drift_analysis.py for the features that
-- are plain mart columns, with the same fills: seller_prior_late_rate missing -> the late rate of all orders up to
-- 2018-02 (the training-period prior); distance_km missing -> its overall median. Months 2017-03 to 2018-08.
-- AUC by the Mann-Whitney statistic with average ranks for ties:
--   (sum of the late orders' ranks - p * (p + 1) / 2) / (p * q),  p = late orders, q = on-time orders.
with base as (
    select
        to_char(purchase_ts, 'YYYY-MM') as month,
        is_late,
        promised_days,
        distance_km,
        seller_prior_late_rate
    from {{ ref('mart_late_delivery_features') }}
),
fills as (
    select
        avg(iff(month <= '2018-02', is_late::float, null)) as prior,
        median(distance_km) as distance_median
    from base
),
long as (
    select b.month, b.is_late, 'promised_days' as feature, b.promised_days::float as x
    from base b
    union all
    select b.month, b.is_late, 'distance_km', coalesce(b.distance_km, f.distance_median)::float
    from base b cross join fills f
    union all
    select b.month, b.is_late, 'seller_prior_late_rate', coalesce(b.seller_prior_late_rate, f.prior)::float
    from base b cross join fills f
),
ranked as (
    select
        month,
        feature,
        is_late,
        rank() over (partition by month, feature order by x)
            + (count(*) over (partition by month, feature, x) - 1) / 2.0 as avg_rank
    from long
    where month between '2017-03' and '2018-08'
)
select
    month,
    feature,
    count(*) as orders,
    avg(is_late::float) as late_rate,
    (sum(iff(is_late = 1, avg_rank, 0)) - sum(is_late) * (sum(is_late) + 1) / 2.0)
        / nullif(sum(is_late) * (count(*) - sum(is_late)), 0) as roc_auc
from ranked
group by 1, 2
