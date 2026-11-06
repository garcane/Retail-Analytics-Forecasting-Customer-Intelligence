
    
    

select
    product_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_MARTS.dim_product
where product_id is not null
group by product_id
having count(*) > 1


