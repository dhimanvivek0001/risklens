-- 04 Features from instalment payments on past Home Credit loans
-- days_late = payment day - due day (positive = paid late)
-- Note: one instalment can be paid in several parts, so this is payment-level behaviour
-- Grain of output: one row per SK_ID_CURR

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.installments AS
WITH i AS (
    SELECT
        SK_ID_CURR,
        SK_ID_PREV,
        DAYS_INSTALMENT,
        AMT_INSTALMENT,
        AMT_PAYMENT,
        DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT AS days_late
    FROM raw.installments_payments
)
SELECT
    SK_ID_CURR,
    COUNT(*)                                                                      AS inst_payment_count,
    COUNT(DISTINCT SK_ID_PREV)                                                    AS inst_loan_count,
    AVG(CASE WHEN days_late > 0 THEN 1.0 WHEN days_late IS NOT NULL THEN 0.0 END) AS inst_late_share,
    AVG(CASE WHEN days_late > 30 THEN 1.0 WHEN days_late IS NOT NULL THEN 0.0 END) AS inst_late_30_share,
    AVG(GREATEST(days_late, 0))                                                   AS inst_avg_days_late,
    MAX(days_late)                                                                AS inst_max_days_late,
    AVG(CASE WHEN days_late < 0 THEN -days_late END)                              AS inst_avg_days_early,
    AVG(CASE WHEN DAYS_INSTALMENT >= -365 AND days_late > 0 THEN 1.0
             WHEN DAYS_INSTALMENT >= -365 AND days_late IS NOT NULL THEN 0.0 END) AS inst_late_share_12m,
    AVG(CASE WHEN AMT_PAYMENT < AMT_INSTALMENT THEN 1.0
             WHEN AMT_PAYMENT IS NOT NULL THEN 0.0 END)                           AS inst_underpaid_share,
    SUM(GREATEST(AMT_INSTALMENT - AMT_PAYMENT, 0))                                AS inst_underpaid_amount,
    SUM(AMT_PAYMENT) / NULLIF(SUM(AMT_INSTALMENT), 0)                             AS inst_paid_to_due_ratio
FROM i
GROUP BY SK_ID_CURR;