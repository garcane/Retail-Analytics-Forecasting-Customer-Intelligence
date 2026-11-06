-- mart_payments: port of sql/analytics/06_payments.sql (reports/analytics/06_payments.csv).
-- Grain: one row per payment type. fact_payments is analysed on its own: its total need not equal item revenue.
-- Consumers must ORDER BY payment_value DESC. avg_payment is sum / count (one float division of the exact sum), see
-- mart_category_performance.sql for why avg(x::float) is avoided on money columns.
select payment_type,
       count(*)                                                                           as payments,
       round(sum(payment_value), 2)                                                       as payment_value,
       round(100 * sum(payment_value)::float / sum(sum(payment_value)::float) over (), 1) as value_share_pct,
       round(sum(payment_value)::float / count(payment_value), 2)                       as avg_payment,
       round(avg(payment_installments::float), 2)                                         as avg_installments
from {{ ref('fact_payments') }}
group by payment_type
order by payment_value desc nulls last
