-- Singular test: every calendar date used by the staging tables must exist in dim_date, and dim_date must span
-- whole calendar years (first day = 1 January of the earliest used year, last day = 31 December of the latest).
-- Guards the GENERATOR spine in dim_date.sql against ever being too short. Returns the failing rows.
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

missing as (
    select distinct
        'date used but missing from dim_date' as problem,
        to_char(d, 'YYYY-MM-DD')              as detail
    from seen
    where d is not null
      and d not in (select full_date from {{ ref('dim_date') }} where full_date is not null)
),

span as (
    select
        date_trunc('year', min(d))::date                                       as want_first,
        dateadd(day, -1, dateadd(year, 1, date_trunc('year', max(d))))::date   as want_last
    from seen
),

have as (
    select min(full_date) as have_first, max(full_date) as have_last
    from {{ ref('dim_date') }}
    where date_key <> -1
),

bad_span as (
    select
        'calendar span is not whole calendar years around the used dates' as problem,
        to_char(want_first, 'YYYY-MM-DD') || '..' || to_char(want_last, 'YYYY-MM-DD') || ' expected, '
            || to_char(have_first, 'YYYY-MM-DD') || '..' || to_char(have_last, 'YYYY-MM-DD') || ' found' as detail
    from span
    cross join have
    where want_first is distinct from have_first
       or want_last  is distinct from have_last
)

select problem, detail from missing
union all
select problem, detail from bad_span
