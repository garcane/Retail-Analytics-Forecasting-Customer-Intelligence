-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_payment_shares_add_up_and_total_matches_the_fact. Expectations are derived from the fact tables, never hard-coded.
with total as (
    select sum(payment_value) as payment_value, count(*) as payments from {{ ref('fact_payments') }}
), m as (
    select sum(payment_value) as payment_value, sum(payments) as payments, sum(value_share_pct) as share_sum
    from {{ ref('mart_payments') }}
)
select 'payment_value within 0.5' as failed_check, total.payment_value::float as expected, m.payment_value::float as actual from total, m where abs(total.payment_value - m.payment_value) > 0.5
union all select 'payments', total.payments, m.payments from total, m where total.payments != m.payments
union all select 'value shares add up to 100 (+-0.3)', 100, m.share_sum from m where abs(m.share_sum - 100) > 0.3
