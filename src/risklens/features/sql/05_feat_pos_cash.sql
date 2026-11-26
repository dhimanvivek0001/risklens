-- 05 Features from monthly snapshots of past point-of-sale and cash loans
-- Uses a window function to find each loan's most recent month
-- Grain of output: one row per SK_ID_CURR

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.pos_cash AS
WITH monthly AS (
    SELECT
        SK_ID_CURR,
        COUNT(*)                                                            AS pos_months,
        COUNT(DISTINCT SK_ID_PREV)                                          AS pos_loan_count,
        MAX(SK_DPD_DEF)                                                     AS pos_max_dpd,
        AVG(CASE WHEN SK_DPD_DEF > 0 THEN 1.0 ELSE 0.0 END)                 AS pos_dpd_month_share,
        SUM(CASE WHEN SK_DPD_DEF > 0 AND MONTHS_BALANCE >= -12 THEN 1 ELSE 0 END) AS pos_dpd_months_12m
    FROM raw.pos_cash_balance
    GROUP BY SK_ID_CURR
),
latest AS (
    SELECT *
    FROM raw.pos_cash_balance
    QUALIFY ROW_NUMBER() OVER (PARTITION BY SK_ID_PREV ORDER BY MONTHS_BALANCE DESC) = 1
),
latest_agg AS (
    SELECT
        SK_ID_CURR,
        SUM(CNT_INSTALMENT_FUTURE)                                          AS pos_remaining_instalments,
        AVG(CASE WHEN NAME_CONTRACT_STATUS = 'Active' THEN 1.0 ELSE 0.0 END) AS pos_active_share,
        AVG(CASE WHEN NAME_CONTRACT_STATUS = 'Completed' THEN 1.0 ELSE 0.0 END) AS pos_completed_share
    FROM latest
    GROUP BY SK_ID_CURR
)
SELECT m.*, l.pos_remaining_instalments, l.pos_active_share, l.pos_completed_share
FROM monthly m
LEFT JOIN latest_agg l USING (SK_ID_CURR);