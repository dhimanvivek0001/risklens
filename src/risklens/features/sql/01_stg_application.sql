-- 01 Staging: clean application table (train + test together)
-- Grain: one row per application (SK_ID_CURR)

CREATE SCHEMA IF NOT EXISTS staging;

CREATE OR REPLACE TABLE staging.application AS
WITH unioned AS (
    SELECT *, 1 AS is_train FROM raw.application_train
    UNION ALL BY NAME
    SELECT *, 0 AS is_train FROM raw.application_test
),
caps AS (
    SELECT quantile_cont(AMT_INCOME_TOTAL, 0.99) AS income_p99
    FROM raw.application_train
)
SELECT
    u.* EXCLUDE (DAYS_EMPLOYED, AMT_INCOME_TOTAL),
    CASE WHEN u.DAYS_EMPLOYED = 365243 THEN NULL ELSE u.DAYS_EMPLOYED END AS DAYS_EMPLOYED,
    CASE WHEN u.DAYS_EMPLOYED = 365243 THEN 1 ELSE 0 END            AS FLAG_EMPLOYED_PLACEHOLDER,
    LEAST(u.AMT_INCOME_TOTAL, c.income_p99)                          AS AMT_INCOME_TOTAL,
    u.AMT_INCOME_TOTAL                                               AS AMT_INCOME_TOTAL_RAW
FROM unioned u
CROSS JOIN caps c;