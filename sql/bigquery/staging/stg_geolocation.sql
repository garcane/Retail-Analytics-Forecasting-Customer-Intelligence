-- Staging: typed view over the raw geolocation file.
-- Grain: NOT unique. ~1M points for ~19k zip prefixes; collapsed in dimensions/dim_geography.sql.
-- The zip prefix stays STRING so leading zeros (e.g. '01046') survive.
create or replace view `${PROJECT}.staging.stg_geolocation` as
select
    geolocation_zip_code_prefix,
    cast(geolocation_lat as float64) as geolocation_lat,
    cast(geolocation_lng as float64) as geolocation_lng,
    geolocation_city,
    geolocation_state
from `${PROJECT}.raw.olist_geolocation_dataset`;