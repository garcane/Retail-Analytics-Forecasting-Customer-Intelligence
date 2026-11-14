-- mart_monthly_kpis: port of sql/analytics/01_monthly_kpis.sql (reports/analytics/01_monthly_kpis.csv).
-- Grain: one row per purchase month (year_month). Net revenue = item price of orders that were not canceled or
-- unavailable (revenue comes from fact_order_items only). Months below 500 orders are flagged thin_month.
-- Consumers must ORDER BY year_month: a table has no stored row order.
--
-- Snowflake notes
--   * revenue / orders and items * 1.0 / orders: operands cast ::float so the result is a double, as in DuckDB
--     (Snowflake NUMBER / NUMBER uses decimal scale rules and could round differently at .x5 boundaries)
--   * NULLS LAST on the window ordering (Snowflake and DuckDB differ on default NULL placement)
with items as (
    select d.year_month, oi.order_id, oi.customer_key, oi.price, oi.freight_value
    from {{ ref('fact_order_items') }} oi
    join {{ ref('dim_date') }} d on d.date_key = oi.purchase_date_key
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
       round(revenue::float / orders, 2)                                       as avg_order_value,
       round(items::float / orders, 3)                                         as items_per_order,
       -- growth is only meaningful between two months that are both above the thin-month line
       case when orders >= 500 and lag(orders) over (order by year_month nulls last) >= 500
            then round(100 * (revenue::float / lag(revenue::float) over (order by year_month nulls last) - 1), 1) end as revenue_mom_pct,
       orders < 500                                                            as thin_month
from monthly
order by year_month
