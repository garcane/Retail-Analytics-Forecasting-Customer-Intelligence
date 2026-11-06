-- Staging: product category name translation (Portuguese -> English).
-- Port of sql/staging/stg_category_translation.sql.
-- Grain: one row per product_category_name.
-- 2 categories used by products are missing here (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos).
select
    nullif(product_category_name, '')            as product_category_name,
    nullif(product_category_name_english, '')    as product_category_name_english
from RETAIL_OLIST.RAW.product_category_translation