-- dim_geography: one row per Brazilian zip-code prefix.
-- Role-played by the facts: customer location and seller location (a customer's location is taken
-- per order, so the 250 customers who moved between orders are handled without a type-2 dimension).
-- Grain: one row per zip prefix. Key: geography_key (surrogate); -1 = unknown (zip prefix not in geolocation).
-- Source: ~1M geolocation points collapsed to one row per prefix.
--   * points outside a Brazil bounding box are dropped (31 in the source)
--   * latitude / longitude = median of the points
--   * city / state = most frequent value (8 prefixes span more than one state); ties broken alphabetically
create table dim_geography (
    geography_key    BIGINT PRIMARY KEY,
    zip_prefix       VARCHAR UNIQUE,
    city             VARCHAR,
    state            VARCHAR,
    latitude         DOUBLE,
    longitude        DOUBLE,
    n_source_points  INTEGER
);

insert into dim_geography values (-1, null, 'Unknown', 'Unknown', null, null, 0);

insert into dim_geography
with pts as (
    select geolocation_zip_code_prefix as zip_prefix,
           geolocation_lat             as lat,
           geolocation_lng             as lng,
           geolocation_city            as city,
           geolocation_state           as state
    from stg_geolocation
    where geolocation_lat between -34 and 6
      and geolocation_lng between -74 and -28
),
coords as (
    select zip_prefix, median(lat) as latitude, median(lng) as longitude, count(*) as n_points
    from pts group by 1
),
top_state as (
    select zip_prefix, state from (
        select zip_prefix, state,
               row_number() over (partition by zip_prefix order by count(*) desc, state) as rn
        from pts group by 1, 2
    ) where rn = 1
),
top_city as (
    select zip_prefix, city from (
        select zip_prefix, city,
               row_number() over (partition by zip_prefix order by count(*) desc, city) as rn
        from pts group by 1, 2
    ) where rn = 1
)
select
    row_number() over (order by c.zip_prefix),
    c.zip_prefix,
    tc.city,
    ts.state,
    c.latitude,
    c.longitude,
    c.n_points
from coords c
join top_state ts using (zip_prefix)
join top_city  tc using (zip_prefix);
