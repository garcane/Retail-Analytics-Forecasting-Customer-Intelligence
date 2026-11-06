
    
    

with child as (
    select seller_key as from_field
    from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items
    where seller_key is not null
),

parent as (
    select seller_key as to_field
    from RETAIL_OLIST.DBT_CI_MARTS.dim_seller
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


