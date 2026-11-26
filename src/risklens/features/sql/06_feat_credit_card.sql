-- 06 Features from monthly snapshots of past Home Credit credit cards
-- utilisation = balance / credit limit (above 1 = over the limit)
-- Grain of output: one row per SK_ID_CURR

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.credit_card AS
WITH cc AS (
    SELECT *,
        AMT_BALANCE / NULLIF(AMT_CREDIT_LIMIT_ACTUAL, 0) AS utilisation
    FROM raw.credit_card_balance
)
SELECT
    SK_ID_CURR,
    COUNT(DISTINCT SK_ID_PREV)                                          AS cc_card_count,
    COUNT(*)                                                            AS cc_months,
    AVG(utilisation)                                                    AS cc_avg_utilisation,
    MAX(utilisation)                                                    AS cc_max_utilisation,
    AVG(CASE WHEN MONTHS_BALANCE >= -6 THEN utilisation END)            AS cc_avg_utilisation_6m,
    MAX(SK_DPD_DEF)                                                     AS cc_max_dpd,
    AVG(CASE WHEN SK_DPD_DEF > 0 THEN 1.0 ELSE 0.0 END)                 AS cc_dpd_month_share,
    AVG(AMT_PAYMENT_CURRENT / NULLIF(AMT_INST_MIN_REGULARITY, 0))       AS cc_avg_paid_to_minimum,
    AVG(AMT_DRAWINGS_CURRENT)                                           AS cc_avg_drawings,
    MAX(AMT_BALANCE)                                                    AS cc_max_balance
FROM cc
GROUP BY SK_ID_CURR;