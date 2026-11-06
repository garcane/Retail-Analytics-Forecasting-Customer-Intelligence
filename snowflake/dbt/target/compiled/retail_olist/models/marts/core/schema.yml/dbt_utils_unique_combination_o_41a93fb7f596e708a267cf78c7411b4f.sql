





with validation_errors as (

    select
        review_id, order_id
    from RETAIL_OLIST.DBT_CI_MARTS.fact_reviews
    group by review_id, order_id
    having count(*) > 1

)

select *
from validation_errors


