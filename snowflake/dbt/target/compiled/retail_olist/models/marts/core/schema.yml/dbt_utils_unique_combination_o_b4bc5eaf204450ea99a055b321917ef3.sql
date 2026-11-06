





with validation_errors as (

    select
        order_id, order_item_id
    from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items
    group by order_id, order_item_id
    having count(*) > 1

)

select *
from validation_errors


