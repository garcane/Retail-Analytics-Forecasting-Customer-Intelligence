-- Singular test: returns one row per failed check (a passing test returns zero rows).
-- Port of tests/test_analytics.py::test_delivery_trend_covers_the_same_population_as_the_ml_features. Expectations are derived from the fact tables, never hard-coded.
with expected as (
    select count(*) as orders
    from {{ ref('fact_orders') }}
    where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
), m as (
    select sum(delivered_orders) as orders, count(*) as n_rows, count(distinct purchase_month) as n_months
    from {{ ref('mart_delivery_trend') }}
)
select 'delivered_orders equal the labelled population' as failed_check, expected.orders::float as expected, m.orders::float as actual
from expected, m where expected.orders != m.orders
union all select 'purchase_month unique', m.n_rows, m.n_months from m where m.n_rows != m.n_months
