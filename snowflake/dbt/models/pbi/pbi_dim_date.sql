{{ config(alias='dim_date') }}

-- pbi_dim_date: Power BI-facing view, schema PBI, object DIM_DATE. Port of the `dim_date` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
-- The -1 'Not applicable' member (empty date) is left out: the date table's key must have no blanks in Power BI, so
-- facts pointing at -1 fall into Power BI's own (Blank) date member. The other dimensions keep their -1 member.
select
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    year_month,
    day_of_month,
    iso_week,
    day_of_week,
    day_name,
    is_weekend
from {{ ref('dim_date') }}
where full_date is not null
