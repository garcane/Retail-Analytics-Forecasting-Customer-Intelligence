
    
    

with child as (
    select review_answer_date_key as from_field
    from RETAIL_OLIST.DBT_CI_MARTS.fact_reviews
    where review_answer_date_key is not null
),

parent as (
    select date_key as to_field
    from RETAIL_OLIST.DBT_CI_MARTS.dim_date
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


