
    
    

select
    zip_prefix as unique_field,
    count(*) as n_records

from RETAIL_OLIST.DBT_CI_INTERMEDIATE.int_geography_rollup
where zip_prefix is not null
group by zip_prefix
having count(*) > 1


