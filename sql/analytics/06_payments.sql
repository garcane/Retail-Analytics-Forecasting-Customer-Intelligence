-- Payment mix. fact_payments is analysed on its own (DD-04): its total need not equal item revenue.
select payment_type,
       count(*)                                                              as payments,
       round(sum(payment_value), 2)                                          as payment_value,
       round(100 * sum(payment_value) / sum(sum(payment_value)) over (), 1)  as value_share_pct,
       round(avg(payment_value), 2)                                          as avg_payment,
       round(avg(payment_installments), 2)                                   as avg_installments
from fact_payments
group by payment_type
order by payment_value desc;
