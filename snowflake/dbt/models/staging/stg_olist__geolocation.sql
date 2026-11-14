-- Staging: typed view over RAW.GEOLOCATION. Port of sql/staging/stg_geolocation.sql.
-- Grain: NOT unique. ~1M points for ~19k zip prefixes; collapsed in int_geography_points / int_geography_rollup.
-- The zip prefix stays text so leading zeros (e.g. 01046) survive. Coordinates are FLOAT (DuckDB DOUBLE).
select
    nullif(geolocation_zip_code_prefix, '')                 as geolocation_zip_code_prefix,
    cast(nullif(geolocation_lat, '') as float)              as geolocation_lat,
    cast(nullif(geolocation_lng, '') as float)              as geolocation_lng,
    nullif(geolocation_city, '')                            as geolocation_city,
    nullif(geolocation_state, '')                           as geolocation_state
from {{ source('olist_raw', 'geolocation') }}
