-- Singular test: a fact row may carry the -1 unknown key only when the lookup has no match in staging.
-- Catches a join that silently degrades to -1 (e.g. a type or case mismatch). Returns the offending rows.
select 'product_key = -1 although the product exists in staging' as problem, f.order_id, f.order_item_id
from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items f
join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_items i
    on i.order_id = f.order_id and i.order_item_id = f.order_item_id
where f.product_key = -1
  and exists (select 1 from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__products p where p.product_id = i.product_id)

union all

select 'seller_key = -1 although the seller exists in staging', f.order_id, f.order_item_id
from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items f
join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__order_items i
    on i.order_id = f.order_id and i.order_item_id = f.order_item_id
where f.seller_key = -1
  and exists (select 1 from RETAIL_OLIST.DBT_CI_STAGING.stg_olist__sellers s where s.seller_id = i.seller_id)

union all

select 'customer_key = -1 although the customer exists in staging', f.order_id, f.order_item_id
from RETAIL_OLIST.DBT_CI_MARTS.fact_order_items f
join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__orders o on o.order_id = f.order_id
join RETAIL_OLIST.DBT_CI_STAGING.stg_olist__customers c on c.customer_id = o.customer_id
where f.customer_key = -1