-- Staging: typed view over the raw sellers file.
-- Grain: one row per seller (seller_id).
create or replace view stg_sellers as
select *
from read_csv(
    '${DATA_DIR}/olist_sellers_dataset.csv',
    header = true,
    columns = {
        'seller_id': 'VARCHAR',
        'seller_zip_code_prefix': 'VARCHAR',
        'seller_city': 'VARCHAR',
        'seller_state': 'VARCHAR'
    }
);
