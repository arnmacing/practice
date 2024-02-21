with comments_time_series as (
    select
        date_trunc('day', timestamp_msk) as date,
        count(comments) as comment_count
    from {{ ref('data') }}
    where comments is not null
    group by date_trunc('day', timestamp_msk)
    order by date
)

select * from comments_time_series