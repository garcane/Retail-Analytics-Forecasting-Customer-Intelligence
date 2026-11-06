-- int_late_delivery_item_agg: order-level basket and route features built from the items of the population.
-- Port of the `it` and `item_agg` CTEs of sql/ml/late_delivery_features.sql.
-- Grain: one row per order_id of the population that has at least one item.
--
-- Snowflake translation notes
--   * arg_max(category, price) -> deterministic pick, see the INTENTIONAL DIFFERENCE below.
--   * haversine is computed on FLOAT columns (dim_geography.latitude/longitude are float), so Snowflake's NUMBER
--     scale rules never enter the arithmetic. pow() -> power().
--   * sum(coalesce(product_weight_g, 0)) is widened to NUMBER(38,0) by Snowflake; cast to bigint for a stable type.
--
-- INTENTIONAL DIFFERENCE vs the DuckDB query (documented, expected, not a bug)
--   DuckDB's `arg_max(category, price)` picks an arbitrary row when several items share the highest price
--   (57 of the 96,282 labelled orders have a price tie across DIFFERENT categories in warehouse.duckdb). That pick
--   is not reproducible, even in DuckDB. Here ties are broken deterministically by taking the alphabetically first
--   category among the items at the maximum price. Orders without a price tie get exactly the DuckDB category.
--   `category` is not an output column of the feature table, but it keys category_prior_n / category_prior_late, so
--   a different pick in a tied order changes those history counts for that order and for orders that share the
--   affected categories. Expect small diffs in category_prior_* only; reconciliation reports them as diff counts.
with items as (
    select
        oi.order_id,
        oi.seller_key,
        oi.price,
        oi.freight_value,
        p.product_weight_g,
        p.product_volume_cm3,
        p.product_category_name_english                    as category,
        s.seller_state,
        cg.state                                           as customer_state,
        cg.latitude                                        as c_lat,
        cg.longitude                                       as c_lon,
        sg.latitude                                        as s_lat,
        sg.longitude                                       as s_lon,
        max(oi.price) over (partition by oi.order_id)      as order_max_price
    from {{ ref('fact_order_items') }} oi
    join {{ ref('int_late_delivery_population') }} pop
        on pop.order_id = oi.order_id
    join {{ ref('dim_product') }} p
        on p.product_key = oi.product_key
    join {{ ref('dim_seller') }} s
        on s.seller_key = oi.seller_key
    join {{ ref('dim_geography') }} cg
        on cg.geography_key = oi.customer_geography_key
    join {{ ref('dim_geography') }} sg
        on sg.geography_key = oi.seller_geography_key
)

select
    order_id,
    cast(count(distinct seller_key) as bigint)                         as n_sellers,
    cast(sum(coalesce(product_weight_g, 0)) as bigint)                 as total_weight_g,
    max(product_volume_cm3)                                            as max_volume_cm3,
    max(freight_value)                                                 as max_item_freight,
    min(seller_state)                                                  as seller_state,     -- deterministic pick when several sellers
    min(customer_state)                                                as customer_state,
    -- category of the most expensive item; ties on price -> alphabetically first category (see header)
    min(case when price = order_max_price then category end)           as category,
    -- great-circle distance in km (haversine); null when either zip prefix is the unknown member
    max(2 * 6371 * asin(sqrt(
        power(sin(radians(c_lat - s_lat) / 2), 2)
        + cos(radians(s_lat)) * cos(radians(c_lat)) * power(sin(radians(c_lon - s_lon) / 2), 2)
    )))                                                                as distance_km
from items
group by order_id
