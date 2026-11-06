
    
    

select
    customer_unique_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_MARTS.dim_customer
where customer_unique_id is not null
group by customer_unique_id
having count(*) > 1


