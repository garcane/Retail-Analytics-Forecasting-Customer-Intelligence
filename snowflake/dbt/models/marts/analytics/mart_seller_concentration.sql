-- mart_seller_concentration: port of sql/analytics/04_seller_concentration.sql (reports/analytics/04_*.csv).
-- Grain: one row per metric (6 rows: seller count, top-1 / top-10 / top-10% / top-50% revenue share, median seller
-- revenue). Ranked by net item revenue, ties broken by seller_key. A table has no stored row order: the DuckDB
-- output order is the order of the union branches below (count, top 1, top 10, top 10%, top 50%, median).
--
-- Snowflake notes
--   * FILTER (WHERE ...) -> sum(case when ... then revenue end)
--   * ceil(0.1 * n_sellers) keeps 0.1 as an exact decimal literal (a float 0.1 could push ceil() up by one)
--   * every branch of the union casts value ::float (DuckDB: DOUBLE)
with seller_rev as (
    select seller_key, sum(price) as revenue
    from {{ ref('fact_order_items') }}
    where order_status not in ('canceled', 'unavailable')
    group by seller_key
), ranked as (
    select seller_key, revenue,
           row_number() over (order by revenue desc nulls last, seller_key nulls last) as rn,
           count(*) over ()                                      as n_sellers,
           sum(revenue) over ()                                  as total
    from seller_rev
)
select 'sellers with net revenue' as metric, any_value(n_sellers)::float as value from ranked
union all select 'top 1 seller share of revenue (%)',        round(100 * sum(case when rn <= 1 then revenue end)::float / any_value(total)::float, 2)::float from ranked
union all select 'top 10 sellers share of revenue (%)',      round(100 * sum(case when rn <= 10 then revenue end)::float / any_value(total)::float, 2)::float from ranked
union all select 'top 10% of sellers share of revenue (%)',  round(100 * sum(case when rn <= ceil(0.1 * n_sellers) then revenue end)::float / any_value(total)::float, 2)::float from ranked
union all select 'top 50% of sellers share of revenue (%)',  round(100 * sum(case when rn <= ceil(0.5 * n_sellers) then revenue end)::float / any_value(total)::float, 2)::float from ranked
union all select 'median seller revenue',                    round(median(revenue::float), 2)::float from ranked
