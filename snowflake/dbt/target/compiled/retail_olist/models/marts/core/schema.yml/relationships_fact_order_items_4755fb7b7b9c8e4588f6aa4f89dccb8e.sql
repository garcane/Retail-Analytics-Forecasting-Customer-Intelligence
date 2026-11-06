
    
    

with child as (
    select product_key as from_field
    from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items
    where product_key is not null
),

parent as (
    select product_key as to_field
    from RETAIL_OLIST.DBT_CI_MARTS.dim_product
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


