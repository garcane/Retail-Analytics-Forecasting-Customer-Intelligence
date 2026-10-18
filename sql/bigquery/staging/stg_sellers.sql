-- Staging: typed view over the raw sellers file.
-- Grain: one row per seller (seller_id).
-- Every column is already STRING in raw, so no cast is needed.
create or replace view `${PROJECT}.staging.stg_sellers` as
select *
from `${PROJECT}.raw.olist_sellers_dataset`;