-- dim_geography: one row per Brazilian zip-code prefix. Port of sql/dimensions/dim_geography.sql.
-- Role-played by the facts: customer location and seller location (a customer's location is taken per
-- order, so the 250 customers who moved between orders are handled without a type-2 dimension).
-- Grain: one row per zip prefix. Key: geography_key (surrogate); -1 = unknown (zip prefix not in geolocation).
-- Source: ~1M geolocation points collapsed to one row per prefix (see int_geography_rollup):
--   points outside a Brazil bounding box dropped; lat/lng = median; city/state = most frequent value.
select
    cast(-1 as bigint)                as geography_key,
    cast(null as varchar)             as zip_prefix,
    cast('Unknown' as varchar)        as city,
    cast('Unknown' as varchar)        as state,
    cast(null as float)               as latitude,
    cast(null as float)               as longitude,
    cast(0 as integer)                as n_source_points

union all

select
    cast(row_number() over (order by zip_prefix) as bigint) as geography_key,
    zip_prefix,
    city,
    state,
    latitude,
    longitude,
    cast(n_points as integer) as n_source_points
from RETAIL_OLIST.DBT_CI_INTERMEDIATE.int_geography_rollup