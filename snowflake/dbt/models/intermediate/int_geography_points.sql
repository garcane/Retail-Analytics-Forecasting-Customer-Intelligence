-- int_geography_points: geolocation points inside a Brazil bounding box (lat -34..6, lng -74..-28).
-- Logic lifted from the `pts` CTE of sql/dimensions/dim_geography.sql. 31 source points fall outside the box.
-- Grain: still one row per source point (not unique).
select
    geolocation_zip_code_prefix as zip_prefix,
    geolocation_lat             as lat,
    geolocation_lng             as lng,
    geolocation_city            as city,
    geolocation_state           as state
from {{ ref('stg_olist__geolocation') }}
where geolocation_lat between -34 and 6
  and geolocation_lng between -74 and -28
