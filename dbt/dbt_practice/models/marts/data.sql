with source_data as (

    select
        md5(_id) as hashed_id,
        md5(name) as hashed_name,
        md5(email) as hashed_email,
        timestamp at time zone 'UTC' as timestamp_utc,
        timestamp at time zone 'UTC' at time zone 'Europe/Moscow' as timestamp_msk,
        status,
        round(score::numeric, 2) as score,
        comments,
        origin::json as origin,
        round(age) as age,
        additional_info::json as additional_info,
        transaction_time at time zone 'UTC' as transaction_time_utc,
        transaction_time at time zone 'UTC' at time zone 'Europe/Moscow' as transaction_time_msk,
        data_source
    from {{ ref('raw_data') }}

)

select * from source_data