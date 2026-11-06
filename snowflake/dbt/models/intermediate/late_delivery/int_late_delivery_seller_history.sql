-- int_late_delivery_seller_history: point-in-time seller track record for each order of the population.
-- Port of the `seller_orders`, `this_seller`, `seller_hist` and `seller_agg` CTEs of sql/ml/late_delivery_features.sql.
-- Grain: one row per order_id of the population that has at least one item.
--
-- Point-in-time rule (docs/ml/LEAKAGE_ANALYSIS.md): only orders whose OUTCOME was already known before this
-- purchase are counted, i.e. h.delivered_customer_ts < this order's purchase_ts. The condition is on the delivery
-- time, not on the purchase time: an earlier order still in transit has no outcome yet. The comparison is strict
-- ("<"), so nothing delivered at the same instant is visible, and `h.order_id <> t.order_id` keeps an order from
-- ever counting itself.
--
-- Deliberate asymmetry kept from the DuckDB query: the seller's history (`seller_orders`) filters only on
-- delivered + labelled and therefore INCLUDES timestamp-anomaly orders, while the scored population excludes them.
--
-- Columns
--   seller_prior_n          min over the order's sellers of the number of resolved prior orders (NULL never
--                           happens for orders with items; the mart coalesces to 0 anyway, as DuckDB does)
--   seller_prior_late_rate  mean over the order's sellers of each seller's prior late rate, counting only sellers with
--                           at least 5 resolved prior orders; NULL when no seller qualifies. The training code falls
--                           back to the global rate.
--
-- Snowflake translation notes: avg(is_late::integer) -> avg of a FLOAT cast (Snowflake AVG over integers would
-- return NUMBER(…,6)); FILTER (WHERE n_prior >= 5) -> CASE inside the aggregate. This is a seller-keyed range join
-- (equality on seller_key + inequality on time); on live Snowflake watch its runtime (see README_LIVE_CHECKS.md).
with seller_orders as (
    select distinct
        oi.seller_key,
        o.order_id,
        o.delivered_customer_ts,
        o.is_late
    from {{ ref('fact_order_items') }} oi
    join {{ ref('fact_orders') }} o
        on o.order_id = oi.order_id
    where o.order_status = 'delivered'
      and o.is_late is not null
),

this_seller as (
    select distinct
        oi.order_id,
        oi.seller_key,
        pop.purchase_ts
    from {{ ref('fact_order_items') }} oi
    join {{ ref('int_late_delivery_population') }} pop
        on pop.order_id = oi.order_id
),

seller_hist as (
    select
        t.order_id,
        t.seller_key,
        count(h.order_id)                              as n_prior,
        avg(cast(h.is_late as integer)::float)         as prior_late_rate
    from this_seller t
    left join seller_orders h
        on h.seller_key = t.seller_key
       and h.delivered_customer_ts < t.purchase_ts
       and h.order_id <> t.order_id
    group by t.order_id, t.seller_key
)

select
    order_id,
    cast(min(n_prior) as bigint)                                               as seller_prior_n,
    -- ignore sellers with fewer than 5 resolved orders; training code falls back to the global rate
    avg(case when n_prior >= 5 then prior_late_rate end)                       as seller_prior_late_rate
from seller_hist
group by order_id
