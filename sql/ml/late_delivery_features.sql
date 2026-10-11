-- Feature table for the late-delivery model (D-007). One row per delivered order.
-- Prediction point = purchase_ts. Every column is allowed or point-in-time per docs/ml/LEAKAGE_ANALYSIS.md.
-- Excluded on purpose: carrier/delivery timestamps, delivery_days, delivery_delay_days, order_status (population
-- filter only), has_timestamp_anomaly (row filter only), shipping_limit_date, every review column.
-- delivered_customer_ts is returned only so the training code can drop rows whose outcome was not yet known at the
-- start of a test period. It is never a feature.

with pop as (
    select order_id, customer_key, customer_geography_key, purchase_ts, estimated_delivery_ts, delivered_customer_ts,
           is_late, item_count, items_price, items_freight, payment_count
    from fact_orders
    where order_status = 'delivered'
      and is_late is not null
      and not has_timestamp_anomaly
),

-- item level: one row per (order, item) with product, seller and both locations
it as (
    select oi.order_id, oi.seller_key, oi.price, oi.freight_value,
           p.product_weight_g, p.product_volume_cm3, p.product_photos_qty, p.product_category_name_english as category,
           s.seller_state,
           cg.state as customer_state, cg.latitude as c_lat, cg.longitude as c_lon,
           sg.latitude as s_lat, sg.longitude as s_lon
    from fact_order_items oi
    join pop using (order_id)
    join dim_product p   on p.product_key = oi.product_key
    join dim_seller s    on s.seller_key = oi.seller_key
    join dim_geography cg on cg.geography_key = oi.customer_geography_key
    join dim_geography sg on sg.geography_key = oi.seller_geography_key
),

item_agg as (
    select order_id,
           count(distinct seller_key)               as n_sellers,
           sum(coalesce(product_weight_g, 0))       as total_weight_g,
           max(product_volume_cm3)                  as max_volume_cm3,
           max(freight_value)                       as max_item_freight,
           min(seller_state)                        as seller_state,        -- deterministic pick when several sellers
           min(customer_state)                      as customer_state,
           arg_max(category, price)                 as category,            -- category of the most expensive item
           -- great-circle distance in km (haversine); null when either zip prefix is the unknown member
           max(2 * 6371 * asin(sqrt(
               pow(sin(radians(c_lat - s_lat) / 2), 2)
               + cos(radians(s_lat)) * cos(radians(c_lat)) * pow(sin(radians(c_lon - s_lon) / 2), 2)
           )))                                      as distance_km
    from it
    group by order_id
),

pay as (
    select order_id,
           max(payment_installments) as max_installments,
           arg_max(payment_type, payment_value) as main_payment_type
    from fact_payments
    group by order_id
),

-- Point-in-time seller history: only orders whose outcome was already known (delivered) before this purchase.
-- Condition is on delivered_customer_ts, not purchase_ts: an earlier order still in transit has no outcome yet.
seller_orders as (
    select distinct oi.seller_key, o.order_id, o.delivered_customer_ts, o.is_late
    from fact_order_items oi
    join fact_orders o using (order_id)
    where o.order_status = 'delivered' and o.is_late is not null
),
this_seller as (
    select distinct i.order_id, i.seller_key, pop.purchase_ts
    from it i join pop using (order_id)
),
seller_hist as (
    select t.order_id, t.seller_key,
           count(h.order_id)          as n_prior,
           avg(h.is_late::integer)    as prior_late_rate
    from this_seller t
    left join seller_orders h
           on h.seller_key = t.seller_key
          and h.delivered_customer_ts < t.purchase_ts
          and h.order_id <> t.order_id
    group by t.order_id, t.seller_key
),
seller_agg as (
    select order_id,
           min(n_prior)                                           as seller_prior_n,
           -- ignore sellers with fewer than 5 resolved orders; training code falls back to the global rate
           avg(prior_late_rate) filter (where n_prior >= 5)       as seller_prior_late_rate
    from seller_hist
    group by order_id
),
-- Point-in-time route, category and system-wide history. For each key, the running totals of orders whose outcome was
-- already known are built once, ordered by delivery time, and an ASOF join reads the totals as of each purchase.
-- The join condition is strict (purchase_ts > delivered_customer_ts), so an order never sees itself or anything still
-- in transit. Counts and late totals are returned; smoothing toward a prior is done in the training code, where the
-- prior can be taken from the training period only.
keyed as (
    select pop.order_id, pop.purchase_ts, pop.delivered_customer_ts, pop.is_late,
           coalesce(ia.seller_state, 'unknown') || '>' || coalesce(ia.customer_state, 'unknown') as route,
           coalesce(ia.category, 'unknown') as category
    from pop join item_agg ia using (order_id)
),
cum_route as (
    select route, ts, sum(cnt) over w as n, sum(late) over w as late
    from (select route, delivered_customer_ts as ts, count(*) as cnt, sum(is_late::integer) as late
          from keyed group by 1, 2)
    window w as (partition by route order by ts)
),
cum_category as (
    select category, ts, sum(cnt) over w as n, sum(late) over w as late
    from (select category, delivered_customer_ts as ts, count(*) as cnt, sum(is_late::integer) as late
          from keyed group by 1, 2)
    window w as (partition by category order by ts)
),
cum_all as (
    select ts, sum(cnt) over w as n, sum(late) over w as late
    from (select delivered_customer_ts as ts, count(*) as cnt, sum(is_late::integer) as late from keyed group by 1)
    window w as (order by ts)
),
history as (
    select k.order_id,
           coalesce(r.n, 0)    as route_prior_n,    coalesce(r.late, 0)    as route_prior_late,
           coalesce(c.n, 0)    as category_prior_n, coalesce(c.late, 0)    as category_prior_late,
           -- trailing 28 days of resolved orders system-wide: totals now minus totals 28 days ago
           coalesce(a.n, 0) - coalesce(a28.n, 0)       as recent_n_28d,
           coalesce(a.late, 0) - coalesce(a28.late, 0) as recent_late_28d
    from keyed k
    asof left join cum_route r    on k.route = r.route and k.purchase_ts > r.ts
    asof left join cum_category c on k.category = c.category and k.purchase_ts > c.ts
    asof left join cum_all a      on k.purchase_ts > a.ts
    asof left join cum_all a28    on k.purchase_ts - interval 28 day > a28.ts
)

select
    pop.order_id,
    pop.purchase_ts,
    pop.delivered_customer_ts,
    pop.is_late::integer                                              as is_late,
    -- calendar (known at purchase)
    isodow(pop.purchase_ts)                                           as purchase_dow,
    hour(pop.purchase_ts)                                             as purchase_hour,
    month(pop.purchase_ts)                                            as purchase_month,
    -- the promise shown to the customer
    date_diff('second', pop.purchase_ts, pop.estimated_delivery_ts) / 86400.0 as promised_days,
    -- basket
    pop.item_count, pop.items_price, pop.items_freight,
    pop.items_freight / nullif(pop.items_price, 0)                    as freight_ratio,
    ia.n_sellers, ia.total_weight_g, ia.max_volume_cm3, ia.max_item_freight,
    -- route
    ia.distance_km,
    coalesce(ia.customer_state, 'unknown')                            as customer_state,
    coalesce(ia.seller_state, 'unknown')                              as seller_state,
    (ia.customer_state = ia.seller_state)::integer                    as same_state,
    -- payment chosen at checkout
    py.max_installments,
    coalesce(py.main_payment_type, 'unknown')                         as main_payment_type,
    -- point-in-time seller history
    coalesce(sa.seller_prior_n, 0)                                    as seller_prior_n,
    sa.seller_prior_late_rate,
    -- point-in-time route (seller state > customer state), category and system-wide history (counts and late totals)
    h.route_prior_n, h.route_prior_late, h.category_prior_n, h.category_prior_late,
    h.recent_n_28d, h.recent_late_28d
from pop
join item_agg ia using (order_id)
left join pay py using (order_id)
left join seller_agg sa using (order_id)
join history h using (order_id)
order by pop.purchase_ts, pop.order_id;
