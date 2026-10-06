-- Staging: typed view over the raw order payments file.
-- Grain: one row per payment (order_id, payment_sequential).
create or replace view stg_order_payments as
select *
from read_csv(
    '${DATA_DIR}/olist_order_payments_dataset.csv',
    header = true,
    columns = {
        'order_id': 'VARCHAR',
        'payment_sequential': 'INTEGER',
        'payment_type': 'VARCHAR',
        'payment_installments': 'INTEGER',
        'payment_value': 'DECIMAL(12,2)'
    }
);
