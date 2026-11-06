{#-
  int_late_delivery_history: point-in-time route, category and system-wide delivery history for each order.
  Port of the `keyed`, `cum_route`, `cum_category`, `cum_all` and `history` CTEs of sql/ml/late_delivery_features.sql.
  Grain: one row per order_id of the population that has at least one item.

  Method. For each key (route = seller state > customer state; category; system-wide) the running totals of orders whose
  outcome was already known are built once, ordered by delivery time, and each order reads the totals AS OF its purchase.
  The match is STRICT (purchase_ts > delivered_customer_ts): an order never sees its own outcome, nor anything delivered at
  the same instant, nor anything still in transit. Counts and late totals are returned; smoothing toward a prior is done in
  the training code, where the prior can be taken from the training period only.

  Two interchangeable implementations of the "as of" read, selected with a dbt var (default: asof):

    dbt build -s +mart_late_delivery_features                                                       (ASOF JOIN, default)
    dbt build -s +mart_late_delivery_features --vars '{late_delivery_history_method: range_join}'   (fallback)

  asof        Snowflake ASOF JOIN ... MATCH_CONDITION, a direct port of the DuckDB `ASOF LEFT JOIN`.
              NEEDS LIVE VERIFICATION (snowflake/dbt/README_LIVE_CHECKS.md): it has never run on Snowflake.
  range_join  FALLBACK. LEFT JOIN on the key + `r.ts < k.purchase_ts`, then `qualify row_number() ... = 1` picks the latest
              earlier total. One CTE per lookup so the four joins never multiply rows. Semantically identical, but the
              join is quadratic per key: the system-wide lookups pair every order with every earlier delivery timestamp
              (about 96k x 48k candidate rows before the qualify). Use it only if the live ASOF JOIN fails or behaves
              differently, and expect a much longer runtime than the ASOF version.

  The purchase_ts - 28 days value is precomputed as a plain column (purchase_ts_minus_28d) because MATCH_CONDITION takes
  column references, not expressions.

  Note: with explicit `rows between unbounded preceding and current row` frames the window result equals DuckDB's default
  RANGE frame ONLY because (key, ts) is unique after the GROUP BY in each cum_* input. Keep that GROUP BY ahead of the window.
-#}
{%- set method = var('late_delivery_history_method', 'asof') -%}
{%- if method not in ['asof', 'range_join'] -%}
    {{ exceptions.raise_compiler_error("var late_delivery_history_method must be 'asof' or 'range_join', got: " ~ method) }}
{%- endif -%}

with keyed as (
    select
        pop.order_id,
        pop.purchase_ts,
        dateadd(day, -28, pop.purchase_ts)                                                       as purchase_ts_minus_28d,
        pop.delivered_customer_ts,
        pop.is_late,
        datediff(second, pop.purchase_ts, pop.delivered_customer_ts)::float / 86400.0            as days_to_deliver,
        coalesce(ia.seller_state, 'unknown') || '>' || coalesce(ia.customer_state, 'unknown')    as route,
        coalesce(ia.category, 'unknown')                                                         as category
    from {{ ref('int_late_delivery_population') }} pop
    join {{ ref('int_late_delivery_item_agg') }} ia
        on ia.order_id = pop.order_id
),

-- Running totals per key, ordered by delivery time. (key, ts) is unique after the group by, so a ROWS frame is
-- equivalent to DuckDB's default RANGE frame.
cum_route as (
    select
        route,
        ts,
        sum(cnt)  over (partition by route order by ts rows between unbounded preceding and current row) as n,
        sum(late) over (partition by route order by ts rows between unbounded preceding and current row) as late,
        sum(days) over (partition by route order by ts rows between unbounded preceding and current row) as days
    from (
        select
            route,
            delivered_customer_ts                    as ts,
            count(*)                                 as cnt,
            sum(cast(is_late as integer))            as late,
            sum(days_to_deliver)                     as days
        from keyed
        group by route, delivered_customer_ts
    ) per_ts
),

cum_category as (
    select
        category,
        ts,
        sum(cnt)  over (partition by category order by ts rows between unbounded preceding and current row) as n,
        sum(late) over (partition by category order by ts rows between unbounded preceding and current row) as late
    from (
        select
            category,
            delivered_customer_ts                    as ts,
            count(*)                                 as cnt,
            sum(cast(is_late as integer))            as late
        from keyed
        group by category, delivered_customer_ts
    ) per_ts
),

cum_all as (
    select
        ts,
        sum(cnt)  over (order by ts rows between unbounded preceding and current row) as n,
        sum(late) over (order by ts rows between unbounded preceding and current row) as late,
        sum(days) over (order by ts rows between unbounded preceding and current row) as days
    from (
        select
            delivered_customer_ts                    as ts,
            count(*)                                 as cnt,
            sum(cast(is_late as integer))            as late,
            sum(days_to_deliver)                     as days
        from keyed
        group by delivered_customer_ts
    ) per_ts
),

{% if method == 'asof' -%}
-- ASOF implementation (default). Needs live verification, see header.
history as (
    select
        k.order_id,
        coalesce(r.n, 0)    as route_prior_n,
        coalesce(r.late, 0) as route_prior_late,
        coalesce(r.days, 0) as route_prior_days,    -- total days purchase-to-delivery over the route's resolved orders
        coalesce(c.n, 0)    as category_prior_n,
        coalesce(c.late, 0) as category_prior_late,
        -- trailing 28 days of resolved orders system-wide: totals now minus totals 28 days ago
        coalesce(a.n, 0)    - coalesce(a28.n, 0)    as recent_n_28d,
        coalesce(a.late, 0) - coalesce(a28.late, 0) as recent_late_28d,
        coalesce(a.days, 0) - coalesce(a28.days, 0) as recent_days_28d
    from keyed k
    asof join cum_route r
        match_condition (k.purchase_ts > r.ts)
        on k.route = r.route
    asof join cum_category c
        match_condition (k.purchase_ts > c.ts)
        on k.category = c.category
    asof join cum_all a
        match_condition (k.purchase_ts > a.ts)
    asof join cum_all a28
        match_condition (k.purchase_ts_minus_28d > a28.ts)
)
{%- else -%}
-- FALLBACK implementation (var late_delivery_history_method = range_join): range join + qualify row_number() = 1.
route_asof as (
    select k.order_id, r.n, r.late, r.days
    from keyed k
    left join cum_route r
        on r.route = k.route
       and r.ts < k.purchase_ts
    qualify row_number() over (partition by k.order_id order by r.ts desc nulls last) = 1
),

category_asof as (
    select k.order_id, c.n, c.late
    from keyed k
    left join cum_category c
        on c.category = k.category
       and c.ts < k.purchase_ts
    qualify row_number() over (partition by k.order_id order by c.ts desc nulls last) = 1
),

all_asof as (
    select k.order_id, a.n, a.late, a.days
    from keyed k
    left join cum_all a
        on a.ts < k.purchase_ts
    qualify row_number() over (partition by k.order_id order by a.ts desc nulls last) = 1
),

all_28d_asof as (
    select k.order_id, a.n, a.late, a.days
    from keyed k
    left join cum_all a
        on a.ts < k.purchase_ts_minus_28d
    qualify row_number() over (partition by k.order_id order by a.ts desc nulls last) = 1
),

history as (
    select
        k.order_id,
        coalesce(r.n, 0)    as route_prior_n,
        coalesce(r.late, 0) as route_prior_late,
        coalesce(r.days, 0) as route_prior_days,
        coalesce(c.n, 0)    as category_prior_n,
        coalesce(c.late, 0) as category_prior_late,
        coalesce(a.n, 0)    - coalesce(a28.n, 0)    as recent_n_28d,
        coalesce(a.late, 0) - coalesce(a28.late, 0) as recent_late_28d,
        coalesce(a.days, 0) - coalesce(a28.days, 0) as recent_days_28d
    from keyed k
    left join route_asof r      on r.order_id = k.order_id
    left join category_asof c   on c.order_id = k.order_id
    left join all_asof a        on a.order_id = k.order_id
    left join all_28d_asof a28  on a28.order_id = k.order_id
)
{%- endif %}

select
    order_id,
    cast(route_prior_n as bigint)        as route_prior_n,
    cast(route_prior_late as bigint)     as route_prior_late,
    route_prior_days,
    cast(category_prior_n as bigint)     as category_prior_n,
    cast(category_prior_late as bigint)  as category_prior_late,
    cast(recent_n_28d as bigint)         as recent_n_28d,
    cast(recent_late_28d as bigint)      as recent_late_28d,
    recent_days_28d
from history
