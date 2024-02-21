with avg_age_score as (
    select
        data_source,
        avg(age) as average_age,
        avg(score) as average_score
    from {{ ref('data') }}
    group by data_source
)

select * from avg_age_score