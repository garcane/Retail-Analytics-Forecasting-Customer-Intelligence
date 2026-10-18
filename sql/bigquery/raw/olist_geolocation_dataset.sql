-- Raw: external table over the immutable geolocation CSV in Cloud Storage
-- (the largest file, about 1,000,163 rows).
-- Translates the read_csv(columns = {...}) block of sql/staging/stg_geolocation.sql.
-- The zip prefix is read as text so leading zeros (e.g. '01046') survive;
-- lat / lng are cast to FLOAT64 in the staging view.
create or replace external table `${PROJECT}.raw.olist_geolocation_dataset` (
    geolocation_zip_code_prefix string,  -- STRING so '01037' keeps its leading zero
    geolocation_lat             string,  -- FLOAT64 in staging.stg_geolocation
    geolocation_lng             string,  -- FLOAT64 in staging.stg_geolocation
    geolocation_city            string,
    geolocation_state           string
)
options (
    format                = 'CSV',
    uris                  = ['gs://${BUCKET}/raw/olist/olist_geolocation_dataset.csv'],
    skip_leading_rows     = 1,
    allow_quoted_newlines = true  -- DuckDB's reader accepts line breaks inside quotes by default
);