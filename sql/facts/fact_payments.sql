-- fact_payments: one row per payment instalment record.
-- Grain: one row per (order_id, payment_sequential). An order can have up to 29 payments.
-- Payments carry no date of their own, so purchase_date_key is the order's purchase date.
-- payment_value does NOT always equal items + freight (380 of 98,665 orders differ, mostly instalment
-- orders), so revenue is measured from fact_order_items and payments are analysed here, never forced to tie.
create table fact_payments (
    order_id             VARCHAR NOT NULL,   -- degenerate
    payment_sequential   INTEGER NOT NULL,   -- degenerate
    customer_key         BIGINT  NOT NULL REFERENCES dim_customer (customer_key),
    purchase_date_key    INTEGER NOT NULL REFERENCES dim_date (date_key),
    payment_type         VARCHAR NOT NULL,   -- degenerate: 5 values (credit_card, boleto, voucher, debit_card, not_defined)
    payment_installments INTEGER NOT NULL,
    payment_value        DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

insert into fact_payments
select
    p.order_id,
    p.payment_sequential,
    coalesce(dc.customer_key, -1),
    coalesce(strftime(o.order_purchase_timestamp, '%Y%m%d')::integer, -1),
    p.payment_type,
    p.payment_installments,
    p.payment_value
from stg_order_payments p
join stg_orders o         on o.order_id = p.order_id
left join stg_customers c on c.customer_id = o.customer_id
left join dim_customer dc on dc.customer_unique_id = c.customer_unique_id;
