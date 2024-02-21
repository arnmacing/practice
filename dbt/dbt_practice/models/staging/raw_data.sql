{{ config(
    materialized='incremental',
    unique_key='_id',
    schema='staging'
) }}

{{ config(
    materialized='incremental',
    unique_key='_id',
    schema='staging'
) }}

WITH source AS (
  SELECT
    *
  FROM
    {{ ref('last_upload') }}
)

SELECT
  s.*
FROM
  source s
{% if is_incremental() %}
WHERE
  s.transaction_time > (SELECT MAX(transaction_time) FROM {{ this }})
{% endif %}


