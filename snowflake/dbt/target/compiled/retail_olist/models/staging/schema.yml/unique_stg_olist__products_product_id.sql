
    
    

select
    product_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__products
where product_id is not null
group by product_id
having count(*) > 1


