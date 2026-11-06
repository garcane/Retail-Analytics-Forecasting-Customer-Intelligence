
    
    

select
    seller_id as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__sellers
where seller_id is not null
group by seller_id
having count(*) > 1


