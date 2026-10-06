-- Staging: typed view over the raw geolocation file (parquet).
-- Grain: NOT unique. ~1M points for ~19k zip prefixes; collapsed in dimensions/dim_geography.sql.
create or replace view stg_geolocation as
select
    geolocation_zip_code_prefix::VARCHAR as geolocation_zip_code_prefix,
    geolocation_lat::DOUBLE              as geolocation_lat,
    geolocation_lng::DOUBLE              as geolocation_lng,
    geolocation_city::VARCHAR            as geolocation_city,
    geolocation_state::VARCHAR           as geolocation_state
from read_parquet('${DATA_DIR}/olist_geolocation_dataset.parquet');
