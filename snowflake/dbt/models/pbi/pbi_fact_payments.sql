{{ config(alias='fact_payments') }}

-- pbi_fact_payments: Power BI-facing view, schema PBI, object FACT_PAYMENTS. Port of the `fact_payments` export in src/powerbi/export_data.py.
-- Same column names, order and types as the file Power BI loads today, so the Snowflake-patched model needs only a
-- data-source change. Columns are listed explicitly (no select *) so a core-mart column change cannot silently
-- reach the report. No ORDER BY: a view has no row order and Power BI does not need one.
select
    order_id,
    payment_sequential,
    customer_key,
    purchase_date_key,
    payment_type,
    payment_installments,
    payment_value
from {{ ref('fact_payments') }}
