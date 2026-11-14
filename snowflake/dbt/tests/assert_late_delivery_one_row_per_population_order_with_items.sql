-- Singular test: every population order that has items appears exactly once in the history models and in the feature
-- table. Guards the live-verification item "Snowflake ASOF JOIN keeps left rows that have no earlier match": if it
-- behaves as an inner join, the earliest orders vanish and these counts disagree. A passing test returns zero rows.
-- Expectation comes from the facts (population filter + at least one item), not from the intermediate models.
select expected, population_with_items, item_agg, seller_history, history, mart
from (
    select
        (select count(*)
         from {{ ref('fact_orders') }} o
         where o.order_status = 'delivered'
           and o.is_late is not null
           and not o.has_timestamp_anomaly
           and exists (select 1 from {{ ref('fact_order_items') }} oi where oi.order_id = o.order_id)) as expected,
        (select count(*) from {{ ref('int_late_delivery_population') }} p
          where exists (select 1 from {{ ref('fact_order_items') }} oi where oi.order_id = p.order_id)) as population_with_items,
        (select count(*) from {{ ref('int_late_delivery_item_agg') }})       as item_agg,
        (select count(*) from {{ ref('int_late_delivery_seller_history') }}) as seller_history,
        (select count(*) from {{ ref('int_late_delivery_history') }})        as history,
        (select count(*) from {{ ref('mart_late_delivery_features') }})      as mart
)
where expected <> population_with_items
   or expected <> item_agg
   or expected <> seller_history
   or expected <> history
   or expected <> mart
