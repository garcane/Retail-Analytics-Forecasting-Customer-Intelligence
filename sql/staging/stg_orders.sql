-- Staging: typed view over the raw orders file. No cleaning, no re-casing.
-- Grain: one row per order (order_id).
create or replace view stg_orders as
select *
from read_csv(
    '${DATA_DIR}/olist_orders_dataset.csv',
    header = true,
    columns = {
        'order_id': 'VARCHAR',
        'customer_id': 'VARCHAR',
        'order_status': 'VARCHAR',
        'order_purchase_timestamp': 'TIMESTAMP',
        'order_approved_at': 'TIMESTAMP',
        'order_delivered_carrier_date': 'TIMESTAMP',
        'order_delivered_customer_date': 'TIMESTAMP',
        'order_estimated_delivery_date': 'TIMESTAMP'
    }
);
