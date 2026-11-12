-- mart_late_delivery_features: feature table for the late-delivery model (D-007). One row per delivered order.
-- Port of sql/ml/late_delivery_features.sql; output columns, order and logical types are identical to that query.
-- Prediction point = purchase_ts. Every column is allowed or point-in-time per docs/ml/LEAKAGE_ANALYSIS.md.
-- Excluded on purpose: carrier/delivery timestamps, delivery_days, delivery_delay_days, order_status (population
-- filter only), has_timestamp_anomaly (row filter only), shipping_limit_date, every review column.
-- delivered_customer_ts is returned only so the training code can drop rows whose outcome was not yet known at the
-- start of a test period. It is never a feature.
--
-- Built from: int_late_delivery_population, _item_agg, _seller_history, _history (see their headers) plus the payment
-- choice computed here.
--
-- Snowflake translation notes
--   * isodow -> dayofweekiso; date_diff('second', a, b) / 86400.0 -> datediff(second, a, b)::float / 86400.0
--   * items_freight / nullif(items_price, 0) is divided in FLOAT (Snowflake NUMBER division would keep NUMBER scale)
--   * (customer_state = seller_state)::integer stays NULL if either side is NULL (cast, not iff)
--   * Row order: the DuckDB query ends with `order by purchase_ts, order_id`. It is kept, but a Snowflake table does not
--     guarantee row order on read; consumers (src/data_access, training code) must ORDER BY purchase_ts, order_id themselves.
--
-- Differences in mechanism vs the DuckDB query (results are identical; live reconciliation 2026-11-12: 0 diffs):
--   * Ties on price (category, in int_late_delivery_item_agg) and on payment_value (payment_type, here) resolve to the
--     alphabetically first value, the same rule as sql/ml/late_delivery_features.sql. DuckDB's arg_max used to pick
--     arbitrarily (57 category ties), which made its category_prior_* irreproducible; both engines now agree.
--   * The "as of" history read uses Snowflake's ASOF JOIN (or the documented range-join fallback), not DuckDB's ASOF JOIN.
with pop as (
    select * from {{ ref('int_late_delivery_population') }}
),

ia as (
    select * from {{ ref('int_late_delivery_item_agg') }}
),

-- payment chosen at checkout. Ties on the highest payment_value -> alphabetically first payment_type.
pay as (
    select
        order_id,
        max(payment_installments)                                                       as max_installments,
        min(case when payment_value = max_payment_value then payment_type end)          as main_payment_type
    from (
        select
            order_id,
            payment_installments,
            payment_type,
            payment_value,
            max(payment_value) over (partition by order_id) as max_payment_value
        from {{ ref('fact_payments') }}
    ) p
    group by order_id
),

sa as (
    select * from {{ ref('int_late_delivery_seller_history') }}
),

h as (
    select * from {{ ref('int_late_delivery_history') }}
)

select
    pop.order_id,
    pop.purchase_ts,
    pop.delivered_customer_ts,
    cast(pop.is_late as integer)                                       as is_late,
    -- calendar (known at purchase)
    dayofweekiso(pop.purchase_ts)                                      as purchase_dow,
    hour(pop.purchase_ts)                                              as purchase_hour,
    month(pop.purchase_ts)                                             as purchase_month,
    -- the promise shown to the customer
    datediff(second, pop.purchase_ts, pop.estimated_delivery_ts)::float / 86400.0 as promised_days,
    -- basket
    pop.item_count,
    pop.items_price,
    pop.items_freight,
    pop.items_freight::float / nullif(pop.items_price, 0)::float       as freight_ratio,
    ia.n_sellers,
    ia.total_weight_g,
    ia.max_volume_cm3,
    ia.max_item_freight,
    -- route
    ia.distance_km,
    coalesce(ia.customer_state, 'unknown')                             as customer_state,
    coalesce(ia.seller_state, 'unknown')                               as seller_state,
    cast(ia.customer_state = ia.seller_state as integer)               as same_state,
    -- payment chosen at checkout
    py.max_installments,
    coalesce(py.main_payment_type, 'unknown')                          as main_payment_type,
    -- point-in-time seller history
    coalesce(sa.seller_prior_n, 0)                                     as seller_prior_n,
    sa.seller_prior_late_rate,
    -- point-in-time route (seller state > customer state), category and system-wide history (counts and late totals)
    h.route_prior_n,
    h.route_prior_late,
    h.category_prior_n,
    h.category_prior_late,
    h.recent_n_28d,
    h.recent_late_28d,
    -- delivery-time history, for the slack between the promise and how long this route usually takes
    h.route_prior_days,
    h.recent_days_28d
from pop
join ia on ia.order_id = pop.order_id
left join pay py on py.order_id = pop.order_id
left join sa on sa.order_id = pop.order_id
join h on h.order_id = pop.order_id
order by pop.purchase_ts, pop.order_id
