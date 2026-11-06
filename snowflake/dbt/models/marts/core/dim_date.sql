-- dim_date: one row per calendar day, covering whole calendar years around every date the facts use.
-- Port of sql/dimensions/dim_date.sql. Role-played by the facts (purchase, approved, carrier, delivered,
-- estimated, shipping limit, review dates).
-- Grain: one row per day. Key: date_key = yyyymmdd (smart key); -1 = not applicable (missing date).
-- Built from a generated calendar, not from order dates: 2016-11 has no orders but must still exist.
--
-- Snowflake notes
--   * the day spine comes from GENERATOR; seq4() can have gaps, so it is re-numbered with row_number()
--   * MONTHNAME()/DAYNAME() return abbreviations in Snowflake, so full English names are spelled out with
--     DECODE on month() / dayofweekiso() (locale independent)
--   * DuckDB weekofyear() is the ISO week -> weekiso()
with seen as (
    select order_purchase_timestamp::date       as d from {{ ref('stg_olist__orders') }}
    union all select order_approved_at::date              from {{ ref('stg_olist__orders') }}
    union all select order_delivered_carrier_date::date   from {{ ref('stg_olist__orders') }}
    union all select order_delivered_customer_date::date  from {{ ref('stg_olist__orders') }}
    union all select order_estimated_delivery_date::date  from {{ ref('stg_olist__orders') }}
    union all select shipping_limit_date::date            from {{ ref('stg_olist__order_items') }}
    union all select review_creation_date::date           from {{ ref('stg_olist__order_reviews') }}
    union all select review_answer_timestamp::date        from {{ ref('stg_olist__order_reviews') }}
),

bounds as (
    select
        date_trunc('year', min(d))::date                                   as first_day,
        dateadd(day, -1, dateadd(year, 1, date_trunc('year', max(d))))::date as last_day
    from seen
),

spine as (
    -- 10,000 candidate days (~27 years) is far more than the 2016-2020 window; the singular test
    -- dim_date_covers_all_used_dates fails if the spine is ever too short.
    select row_number() over (order by seq4()) - 1 as n
    from table(generator(rowcount => 10000))
),

days as (
    select dateadd(day, spine.n, bounds.first_day)::date as d
    from spine
    cross join bounds
    where dateadd(day, spine.n, bounds.first_day) <= bounds.last_day
)

select
    cast(-1 as integer)                  as date_key,
    cast(null as date)                   as full_date,
    cast(null as integer)                as year,
    cast(null as integer)                as quarter,
    cast(null as integer)                as month,
    cast('Not applicable' as varchar)    as month_name,
    cast('Not applicable' as varchar)    as year_month,
    cast(null as integer)                as day_of_month,
    cast(null as integer)                as iso_week,
    cast(null as integer)                as day_of_week,
    cast('Not applicable' as varchar)    as day_name,
    cast(null as boolean)                as is_weekend

union all

select
    to_char(d, 'YYYYMMDD')::integer                                  as date_key,
    d                                                                as full_date,
    year(d)                                                          as year,
    quarter(d)                                                       as quarter,
    month(d)                                                         as month,
    decode(month(d),
        1, 'January', 2, 'February', 3, 'March', 4, 'April', 5, 'May', 6, 'June',
        7, 'July', 8, 'August', 9, 'September', 10, 'October', 11, 'November', 12, 'December'
    )                                                                as month_name,
    to_char(d, 'YYYY-MM')                                            as year_month,
    day(d)                                                           as day_of_month,
    weekiso(d)                                                       as iso_week,
    dayofweekiso(d)                                                  as day_of_week,
    decode(dayofweekiso(d),
        1, 'Monday', 2, 'Tuesday', 3, 'Wednesday', 4, 'Thursday', 5, 'Friday', 6, 'Saturday', 7, 'Sunday'
    )                                                                as day_name,
    dayofweekiso(d) >= 6                                             as is_weekend
from days
