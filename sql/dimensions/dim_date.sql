-- dim_date: one row per calendar day, covering whole calendar years around every date the facts use.
-- Role-played by the facts (purchase, approved, carrier, delivered, estimated, shipping limit, review dates).
-- Grain: one row per day. Key: date_key = yyyymmdd (smart key); -1 = not applicable (missing date).
-- Built from a generated calendar, not from order dates: 2016-11 has no orders but must still exist.
create table dim_date (
    date_key     INTEGER PRIMARY KEY,
    full_date    DATE,
    year         INTEGER,
    quarter      INTEGER,
    month        INTEGER,
    month_name   VARCHAR,
    year_month   VARCHAR,
    day_of_month INTEGER,
    iso_week     INTEGER,
    day_of_week  INTEGER,   -- ISO: 1 = Monday ... 7 = Sunday
    day_name     VARCHAR,
    is_weekend   BOOLEAN
);

insert into dim_date values
    (-1, null, null, null, null, 'Not applicable', 'Not applicable', null, null, null, 'Not applicable', null);

insert into dim_date
with seen as (
    select order_purchase_timestamp::date       as d from stg_orders
    union all select order_approved_at::date              from stg_orders
    union all select order_delivered_carrier_date::date   from stg_orders
    union all select order_delivered_customer_date::date  from stg_orders
    union all select order_estimated_delivery_date::date  from stg_orders
    union all select shipping_limit_date::date            from stg_order_items
    union all select review_creation_date::date           from stg_order_reviews
    union all select review_answer_timestamp::date        from stg_order_reviews
),
bounds as (
    select date_trunc('year', min(d))::date                                           as first_day,
           (date_trunc('year', max(d)) + interval 1 year - interval 1 day)::date      as last_day
    from seen
),
days as (
    select unnest(generate_series(first_day, last_day, interval 1 day))::date as d from bounds
)
select
    strftime(d, '%Y%m%d')::integer,
    d,
    year(d),
    quarter(d),
    month(d),
    monthname(d),
    strftime(d, '%Y-%m'),
    day(d),
    weekofyear(d),
    isodow(d),
    dayname(d),
    isodow(d) >= 6
from days;
