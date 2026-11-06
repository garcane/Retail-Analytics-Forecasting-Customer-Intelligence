





with validation_errors as (

    select
        order_id, payment_sequential
    from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_payments
    group by order_id, payment_sequential
    having count(*) > 1

)

select *
from validation_errors


