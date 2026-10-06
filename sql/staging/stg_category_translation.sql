-- Staging: product category name translation (Portuguese -> English).
-- Grain: one row per product_category_name. The source file starts with a UTF-8 BOM;
-- the header row is skipped, so the BOM never reaches a column name.
-- 2 categories used by products are missing here (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos).
create or replace view stg_category_translation as
select *
from read_csv(
    '${DATA_DIR}/product_category_name_translation.csv',
    header = true,
    columns = {
        'product_category_name': 'VARCHAR',
        'product_category_name_english': 'VARCHAR'
    }
);
