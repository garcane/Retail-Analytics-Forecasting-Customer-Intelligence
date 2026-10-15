-- How concentrated is revenue across sellers? Ranked by net item revenue.
with seller_rev as (
    select seller_key, sum(price) as revenue
    from fact_order_items
    where order_status not in ('canceled', 'unavailable')
    group by seller_key
), ranked as (
    select seller_key, revenue,
           row_number() over (order by revenue desc, seller_key) as rn,
           count(*) over ()                                      as n_sellers,
           sum(revenue) over ()                                  as total
    from seller_rev
)
select 'sellers with net revenue' as metric, any_value(n_sellers)::double as value from ranked
union all select 'top 1 seller share of revenue (%)',        round(100 * sum(revenue) filter (where rn <= 1) / any_value(total), 2) from ranked
union all select 'top 10 sellers share of revenue (%)',      round(100 * sum(revenue) filter (where rn <= 10) / any_value(total), 2) from ranked
union all select 'top 10% of sellers share of revenue (%)',  round(100 * sum(revenue) filter (where rn <= ceil(0.1 * n_sellers)) / any_value(total), 2) from ranked
union all select 'top 50% of sellers share of revenue (%)',  round(100 * sum(revenue) filter (where rn <= ceil(0.5 * n_sellers)) / any_value(total), 2) from ranked
union all select 'median seller revenue',                    round(median(revenue), 2) from ranked;
