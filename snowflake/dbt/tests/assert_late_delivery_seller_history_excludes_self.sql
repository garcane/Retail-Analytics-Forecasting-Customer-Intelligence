-- Singular test (leakage guard): returns the order rows whose point-in-time seller history differs from an independent
-- recomputation, so a passing test returns zero rows. Mirrors tests/test_feature_leakage.py and the sample recomputations
-- in tests/test_warehouse.py, but covers every order and starts from the staging models, not from the facts.
--
-- Rule recomputed (docs/ml/LEAKAGE_ANALYSIS.md): a seller's history for an order counts only that seller's OTHER orders
-- that were delivered, labelled, and whose delivery timestamp is strictly BEFORE this order's purchase_ts.
-- Hence the order itself (order_id <> self) and anything delivered at the same instant or later is never counted.
-- Seller history keeps timestamp-anomaly orders (as the DuckDB query does); only the scored population excludes them.
-- Sellers with fewer than 5 resolved prior orders are ignored for the rate; the count is the minimum across sellers.
with probe as (
    select order_id, purchase_ts, seller_prior_n, seller_prior_late_rate
    from {{ ref('mart_late_delivery_features') }}
),

probe_sellers as (
    select distinct i.order_id, i.seller_id, p.purchase_ts
    from {{ ref('stg_olist__order_items') }} i
    join probe p
        on p.order_id = i.order_id
),

resolved as (
    select distinct
        i.seller_id,
        o.order_id,
        o.order_delivered_customer_date                                         as delivered_ts,
        (o.order_delivered_customer_date > o.order_estimated_delivery_date)     as late
    from {{ ref('stg_olist__order_items') }} i
    join {{ ref('stg_olist__orders') }} o
        on o.order_id = i.order_id
    where o.order_status = 'delivered'
      and o.order_delivered_customer_date is not null
      and o.order_estimated_delivery_date is not null
),

per_seller as (
    select
        ps.order_id,
        ps.seller_id,
        count(r.order_id)                                                       as n_prior,
        avg(case when r.late then 1.0 else 0.0 end::float)                      as late_rate
    from probe_sellers ps
    left join resolved r
        on r.seller_id = ps.seller_id
       and r.delivered_ts < ps.purchase_ts
       and r.order_id <> ps.order_id
    group by ps.order_id, ps.seller_id
),

expected as (
    select
        order_id,
        min(n_prior)                                                            as seller_prior_n,
        avg(case when n_prior >= 5 then late_rate end)                          as seller_prior_late_rate
    from per_seller
    group by order_id
)

select
    p.order_id,
    p.seller_prior_n          as actual_n,
    e.seller_prior_n          as expected_n,
    p.seller_prior_late_rate  as actual_rate,
    e.seller_prior_late_rate  as expected_rate
from probe p
left join expected e
    on e.order_id = p.order_id
where e.order_id is null
   or p.seller_prior_n is distinct from e.seller_prior_n
   or (p.seller_prior_late_rate is null) <> (e.seller_prior_late_rate is null)
   or abs(p.seller_prior_late_rate - e.seller_prior_late_rate) > 1e-9
