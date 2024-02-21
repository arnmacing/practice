with user_status as (
    select
        status,
        count(*) as user_count
    from {{ ref('data') }}
    group by status
)

select * from user_status