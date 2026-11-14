{{ config(alias='dim_seller') }}

-- pbi_dim_seller: Power BI-facing view, schema PBI, object DIM_SELLER. Port of the `dim_seller` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
select
    seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from {{ ref('dim_seller') }}
