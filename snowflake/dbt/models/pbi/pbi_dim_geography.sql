{{ config(alias='dim_geography') }}

-- pbi_dim_geography: Power BI-facing view, schema PBI, object DIM_GEOGRAPHY. Port of the `dim_geography` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
select
    geography_key,
    zip_prefix,
    city,
    state,
    latitude,
    longitude,
    n_source_points
from {{ ref('dim_geography') }}
