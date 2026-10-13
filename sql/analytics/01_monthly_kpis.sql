-- Monthly KPIs. Net revenue = item price of orders that were not canceled or unavailable (DD-04: revenue comes from
-- fact_order_items only). Freight is reported separately. AOV = net revenue per order that has items.
-- Months before 2017-01 and after 2018-08 are thin tails (see docs/phase0); they are kept and flagged, not hidden.
with items as (
    select d.year_month, oi.order_id, oi.customer_key, oi.price, oi.freight_value
    from fact_order_items oi
    join dim_date d on d.date_key = oi.purchase_date_key
    where oi.order_status not in ('canceled', 'unavailable')
), monthly as (
    select year_month,
           count(distinct order_id)     as orders,
           count(distinct customer_key) as customers,
           count(*)                     as items,
           sum(price)                   as revenue,
           sum(freight_value)           as freight
    from items group by year_month
)
select year_month,
       orders, customers, items,
       round(revenue, 2)                                                       as net_revenue,
       round(freight, 2)                                                       as freight,
       round(revenue / orders, 2)                                              as avg_order_value,
       round(items * 1.0 / orders, 3)                                          as items_per_order,
       -- growth is only meaningful between two months that are both above the thin-month line
       case when orders >= 500 and lag(orders) over (order by year_month) >= 500
            then round(100 * (revenue / lag(revenue) over (order by year_month) - 1), 1) end as revenue_mom_pct,
       orders < 500                                                            as thin_month
from monthly
order by year_month;
