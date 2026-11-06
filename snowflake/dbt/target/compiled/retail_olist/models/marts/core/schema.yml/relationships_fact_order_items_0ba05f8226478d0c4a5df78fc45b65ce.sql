
    
    

with child as (
    select customer_geography_key as from_field
    from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items
    where customer_geography_key is not null
),

parent as (
    select geography_key as to_field
    from RETAIL_OLIST.DBT_CI_MARTS.dim_geography
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


