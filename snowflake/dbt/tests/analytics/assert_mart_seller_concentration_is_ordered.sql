-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_seller_concentration_is_ordered. Expectations are derived from the fact tables, never hard-coded.
with v as (
    select
        max(case when metric = 'sellers with net revenue' then value end)                 as n_sellers,
        max(case when metric = 'top 1 seller share of revenue (%)' then value end)        as top1,
        max(case when metric = 'top 10 sellers share of revenue (%)' then value end)      as top10,
        max(case when metric = 'top 10% of sellers share of revenue (%)' then value end)  as top10pct,
        max(case when metric = 'top 50% of sellers share of revenue (%)' then value end)  as top50pct,
        max(case when metric = 'median seller revenue' then value end)                    as median
    from {{ ref('mart_seller_concentration') }}
), by_seller as (
    select seller_key, sum(price) as revenue
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
    group by seller_key
), expected as (
    select count(*) as n_sellers,
           round(100 * max(revenue)::float / sum(revenue)::float, 2) as top1_share,
           round(median(revenue::float), 2) as median_revenue
    from by_seller
)
select 'seller count equals distinct sellers with net items' as failed_check, expected.n_sellers::float as expected, v.n_sellers as actual
from v, expected where v.n_sellers != expected.n_sellers
union all select 'top 1 share recomputed from the fact', expected.top1_share, v.top1 from v, expected where abs(v.top1 - expected.top1_share) > 0.005
union all select 'median seller revenue recomputed from the fact', expected.median_revenue, v.median from v, expected where abs(v.median - expected.median_revenue) > 0.005
union all select 'shares ordered: 0 < top1 < top10 < 100', 0, v.top1 from v where not (v.top1 > 0 and v.top1 < v.top10 and v.top10 < 100)
union all select 'shares ordered: top10pct < top50pct <= 100', 0, v.top10pct from v where not (v.top10pct < v.top50pct and v.top50pct <= 100)
