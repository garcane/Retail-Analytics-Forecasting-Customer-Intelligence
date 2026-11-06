
    
    

select
    product_category_name as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__category_translation
where product_category_name is not null
group by product_category_name
having count(*) > 1


