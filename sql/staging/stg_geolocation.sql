-- Staging: typed view over the raw geolocation file.
-- Grain: NOT unique. ~1M points for ~19k zip prefixes; collapsed in dimensions/dim_geography.sql.
-- The zip prefix is read as text so leading zeros (e.g. '01046') survive.
create or replace view stg_geolocation as
select *
from read_csv(
    '${DATA_DIR}/olist_geolocation_dataset.csv',
    header = true,
    columns = {
        'geolocation_zip_code_prefix': 'VARCHAR',
        'geolocation_lat': 'DOUBLE',
        'geolocation_lng': 'DOUBLE',
        'geolocation_city': 'VARCHAR',
        'geolocation_state': 'VARCHAR'
    }
);
