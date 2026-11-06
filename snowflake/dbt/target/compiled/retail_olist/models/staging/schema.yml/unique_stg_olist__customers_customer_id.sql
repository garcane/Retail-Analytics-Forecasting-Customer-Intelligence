
    
    

select
    customer_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__customers
where customer_id is not null
group by customer_id
having count(*) > 1


