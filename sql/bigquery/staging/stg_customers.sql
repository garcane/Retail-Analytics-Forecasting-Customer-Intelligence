-- Staging: typed view over the raw customers file.
-- Grain: one row per customer_id, which is per ORDER. customer_unique_id identifies the person.
-- Zip prefixes stay STRING so leading zeros survive (raw reads every column as STRING).
create or replace view `${PROJECT}.staging.stg_customers` as
select *
from `${PROJECT}.raw.olist_customers_dataset`;