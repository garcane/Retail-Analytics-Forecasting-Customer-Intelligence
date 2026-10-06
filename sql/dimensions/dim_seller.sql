-- dim_seller: one row per seller.
-- Grain: one row per seller_id. Key: seller_key (surrogate); -1 = unknown.
create table dim_seller (
    seller_key             BIGINT PRIMARY KEY,
    seller_id              VARCHAR NOT NULL UNIQUE,
    seller_zip_code_prefix VARCHAR,
    seller_city            VARCHAR,
    seller_state           VARCHAR
);

insert into dim_seller values (-1, 'UNKNOWN', null, 'Unknown', 'Unknown');

insert into dim_seller
select row_number() over (order by seller_id),
       seller_id, seller_zip_code_prefix, seller_city, seller_state
from stg_sellers;
