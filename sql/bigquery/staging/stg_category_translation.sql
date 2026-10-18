-- Staging: product category name translation (Portuguese -> English).
-- Grain: one row per product_category_name.
-- 2 categories used by products are missing here (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos).
create or replace view `${PROJECT}.staging.stg_category_translation` as
select *
from `${PROJECT}.raw.product_category_name_translation`;