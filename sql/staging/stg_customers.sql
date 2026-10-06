-- Staging: typed view over the raw customers file.
-- Grain: one row per customer_id, which is per ORDER. customer_unique_id identifies the person.
-- Zip prefixes stay VARCHAR so leading zeros survive.
create or replace view stg_customers as
select *
from read_csv(
    '${DATA_DIR}/olist_customers_dataset.csv',
    header = true,
    columns = {
        'customer_id': 'VARCHAR',
        'customer_unique_id': 'VARCHAR',
        'customer_zip_code_prefix': 'VARCHAR',
        'customer_city': 'VARCHAR',
        'customer_state': 'VARCHAR'
    }
);
