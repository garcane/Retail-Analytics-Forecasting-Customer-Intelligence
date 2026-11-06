
    
    

select
    order_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__orders
where order_id is not null
group by order_id
having count(*) > 1


