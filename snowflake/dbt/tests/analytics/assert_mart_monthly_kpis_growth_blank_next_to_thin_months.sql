-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_monthly_growth_is_blank_next_to_thin_months. Expectations are derived from the fact tables, never hard-coded.
-- growth must be NULL for a thin month, for the first month, and right after a thin month
with m as (
    select year_month, thin_month, revenue_mom_pct,
           lag(thin_month) over (order by year_month nulls last) as previous_thin,
           row_number() over (order by year_month nulls last) as rn
    from {{ ref('mart_monthly_kpis') }}
)
select 'growth should be blank' as failed_check, year_month, revenue_mom_pct
from m
where revenue_mom_pct is not null and (thin_month or rn = 1 or previous_thin)
