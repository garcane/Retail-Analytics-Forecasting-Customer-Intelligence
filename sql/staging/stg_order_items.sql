-- Staging: typed view over the raw order items file.
-- Grain: one row per order item (order_id, order_item_id).
-- Money is read as DECIMAL(12,2) so sums are exact.
create or replace view stg_order_items as
select *
from read_csv(
    '${DATA_DIR}/olist_order_items_dataset.csv',
    header = true,
    columns = {
        'order_id': 'VARCHAR',
        'order_item_id': 'INTEGER',
        'product_id': 'VARCHAR',
        'seller_id': 'VARCHAR',
        'shipping_limit_date': 'TIMESTAMP',
        'price': 'DECIMAL(12,2)',
        'freight_value': 'DECIMAL(12,2)'
    }
);
