
    
    

with all_values as (

    select
        order_status as value_field,
        count(*) as n_records

    from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__orders
    group by order_status

)

select *
from all_values
where value_field not in (
    'approved','canceled','created','delivered','invoiced','processing','shipped','unavailable'
)


