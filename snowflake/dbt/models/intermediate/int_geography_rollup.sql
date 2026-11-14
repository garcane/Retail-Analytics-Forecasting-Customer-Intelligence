-- int_geography_rollup: one row per zip-code prefix. Logic lifted from sql/dimensions/dim_geography.sql.
--   * latitude / longitude = median of the in-bounds points
--   * state / city = most frequent value, ties broken alphabetically (8 prefixes span more than one state).
--     The sort is a binary (code-point) comparison in both DuckDB and Snowflake's default collation.
-- NULL city/state values are counted as their own group, exactly as the DuckDB GROUP BY does.
-- Rank with row_number() over pre-counted groups (rather than a window over an aggregate) so the ordering is explicit.
with coords as (
    select
        zip_prefix,
        median(lat)  as latitude,
        median(lng)  as longitude,
        count(*)     as n_points
    from {{ ref('int_geography_points') }}
    group by zip_prefix
),

state_counts as (
    select zip_prefix, state, count(*) as n
    from {{ ref('int_geography_points') }}
    group by zip_prefix, state
),

top_state as (
    select zip_prefix, state
    from state_counts
    qualify row_number() over (partition by zip_prefix order by n desc, state) = 1
),

city_counts as (
    select zip_prefix, city, count(*) as n
    from {{ ref('int_geography_points') }}
    group by zip_prefix, city
),

top_city as (
    select zip_prefix, city
    from city_counts
    qualify row_number() over (partition by zip_prefix order by n desc, city) = 1
)

select
    c.zip_prefix,
    tc.city,
    ts.state,
    c.latitude,
    c.longitude,
    c.n_points
from coords c
join top_state ts on ts.zip_prefix = c.zip_prefix
join top_city  tc on tc.zip_prefix = c.zip_prefix
