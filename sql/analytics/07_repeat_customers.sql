-- Repeat purchasing, on real people (customer_unique_id, DD-02). Orders that were not canceled or unavailable.
with orders as (
    select customer_key, order_id, items_price
    from fact_orders
    where order_status not in ('canceled', 'unavailable') and item_count > 0 and customer_key <> -1
), per_customer as (
    select customer_key, count(*) as n_orders, sum(items_price) as revenue
    from orders group by customer_key
)
select case when n_orders >= 4 then '4+' else n_orders::varchar end   as orders_placed,
       count(*)                                                       as customers,
       round(100.0 * count(*) / sum(count(*)) over (), 2)             as customer_share_pct,
       round(sum(revenue), 2)                                         as net_revenue,
       round(100 * sum(revenue) / sum(sum(revenue)) over (), 2)       as revenue_share_pct
from per_customer
group by 1
order by 1;
