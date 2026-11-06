-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_seller_concentration_is_ordered. Expectations are derived from the fact tables, never hard-coded.
with v as (
    select
        max(case when metric = 'sellers with net revenue' then value end)                 as n_sellers,
        max(case when metric = 'top 1 seller share of revenue (%)' then value end)        as top1,
        max(case when metric = 'top 10 sellers share of revenue (%)' then value end)      as top10,
        max(case when metric = 'top 10% of sellers share of revenue (%)' then value end)  as top10pct,
        max(case when metric = 'top 50% of sellers share of revenue (%)' then value end)  as top50pct
    from {{ ref('mart_seller_concentration') }}
), expected as (
    select count(distinct seller_key) as n_sellers
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
)
select 'seller count equals distinct sellers with net items' as failed_check, expected.n_sellers::float as expected, v.n_sellers as actual
from v, expected where v.n_sellers != expected.n_sellers
union all select 'shares ordered: 0 < top1 < top10 < 100', 0, v.top1 from v where not (v.top1 > 0 and v.top1 < v.top10 and v.top10 < 100)
union all select 'shares ordered: top10pct < top50pct <= 100', 0, v.top10pct from v where not (v.top10pct < v.top50pct and v.top50pct <= 100)
