{{ config(alias='dim_customer') }}

-- pbi_dim_customer: Power BI-facing view, schema PBI, object DIM_CUSTOMER. Port of the `dim_customer` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
select
    customer_key,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from {{ ref('dim_customer') }}
