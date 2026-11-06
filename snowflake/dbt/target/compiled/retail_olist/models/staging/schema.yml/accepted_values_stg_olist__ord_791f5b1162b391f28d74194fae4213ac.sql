
    
    

with all_values as (

    select
        review_score as value_field,
        count(*) as n_records

    from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_reviews
    group by review_score

)

select *
from all_values
where value_field not in (
    1,2,3,4,5
)


