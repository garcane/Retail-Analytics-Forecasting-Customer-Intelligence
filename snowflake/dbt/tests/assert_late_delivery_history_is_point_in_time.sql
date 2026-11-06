-- Singular test (leakage guard): returns the sampled orders whose route / category / trailing-28-day history differs from a
-- brute-force recomputation, so a passing test returns zero rows. Passes only if the ASOF join (or the range-join
-- fallback) reads totals STRICTLY before the purchase: an order never sees its own outcome, anything delivered at the same
-- instant, or anything still in transit. Mirrors tests/test_feature_leakage.py.
--
-- Brute force = probe x all population orders. To keep it cheap the probe is a deterministic sample: order_ids whose first
-- two hex characters are '00' (about 1/256 of the orders; order_id is an md5 hash, so the sample is effectively random),
-- plus every order whose purchase falls exactly on a delivery instant or on a delivery instant + 28 days.
-- Rules recomputed:
--   route_prior_*     orders on the same seller_state > customer_state route with delivered_customer_ts < purchase_ts
--   category_prior_*  same, by category
--   recent_*_28d      orders (system-wide) with purchase_ts - 28 days <= delivered_customer_ts < purchase_ts
with keyed as (
    select
        pop.order_id,
        pop.purchase_ts,
        pop.delivered_customer_ts,
        pop.is_late,
        datediff(second, pop.purchase_ts, pop.delivered_customer_ts)::float / 86400.0          as days_to_deliver,
        coalesce(ia.seller_state, 'unknown') || '>' || coalesce(ia.customer_state, 'unknown')  as route,
        coalesce(ia.category, 'unknown')                                                       as category
    from {{ ref('int_late_delivery_population') }} pop
    join {{ ref('int_late_delivery_item_agg') }} ia
        on ia.order_id = pop.order_id
),

-- Boundary probes: orders bought at exactly the instant some other order was delivered (or exactly 28 days after it).
-- These are the cases a ">=" instead of ">" would get wrong, and a random sample alone is unlikely to contain them.
boundary as (
    select p.order_id
    from keyed p
    join keyed k
        on k.delivered_customer_ts = p.purchase_ts
    union
    select p.order_id
    from keyed p
    join keyed k
        on k.delivered_customer_ts = dateadd(day, -28, p.purchase_ts)
),

probe as (
    select * from keyed
    where substr(order_id, 1, 2) = '00'
       or order_id in (select order_id from boundary)
),

expected as (
    select
        p.order_id,
        sum(case when k.route = p.route and k.delivered_customer_ts < p.purchase_ts then 1 else 0 end)                     as route_prior_n,
        sum(case when k.route = p.route and k.delivered_customer_ts < p.purchase_ts and k.is_late then 1 else 0 end)        as route_prior_late,
        sum(case when k.route = p.route and k.delivered_customer_ts < p.purchase_ts then k.days_to_deliver else 0 end)      as route_prior_days,
        sum(case when k.category = p.category and k.delivered_customer_ts < p.purchase_ts then 1 else 0 end)                as category_prior_n,
        sum(case when k.category = p.category and k.delivered_customer_ts < p.purchase_ts and k.is_late then 1 else 0 end)  as category_prior_late,
        sum(case when k.delivered_customer_ts < p.purchase_ts
                  and k.delivered_customer_ts >= dateadd(day, -28, p.purchase_ts) then 1 else 0 end)                        as recent_n_28d,
        sum(case when k.delivered_customer_ts < p.purchase_ts
                  and k.delivered_customer_ts >= dateadd(day, -28, p.purchase_ts) and k.is_late then 1 else 0 end)          as recent_late_28d,
        sum(case when k.delivered_customer_ts < p.purchase_ts
                  and k.delivered_customer_ts >= dateadd(day, -28, p.purchase_ts) then k.days_to_deliver else 0 end)        as recent_days_28d
    from probe p
    cross join keyed k
    group by p.order_id
),

mismatches as (
    select m.order_id
    from {{ ref('mart_late_delivery_features') }} m
    join expected e
        on e.order_id = m.order_id
    where m.route_prior_n is distinct from e.route_prior_n
       or m.route_prior_late is distinct from e.route_prior_late
       or m.category_prior_n is distinct from e.category_prior_n
       or m.category_prior_late is distinct from e.category_prior_late
       or m.recent_n_28d is distinct from e.recent_n_28d
       or m.recent_late_28d is distinct from e.recent_late_28d
       or abs(m.route_prior_days - e.route_prior_days) > 1e-6
       or abs(m.recent_days_28d - e.recent_days_28d) > 1e-6
)

select order_id, 'history differs from brute-force recomputation' as problem
from mismatches

union all

-- guard against a vacuous pass: the sample must not be empty
select cast(null as varchar), 'sample is empty'
from (select count(*) as n from probe)
where n = 0
