-- 03 Features from previous applications to Home Credit
-- Grain of output: one row per SK_ID_CURR

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.previous AS
SELECT
    SK_ID_CURR,
    COUNT(*)                                                                    AS prev_app_count,
    SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Approved' THEN 1 ELSE 0 END)          AS prev_approved_count,
    SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Refused'  THEN 1 ELSE 0 END)          AS prev_refused_count,
    AVG(CASE WHEN NAME_CONTRACT_STATUS = 'Refused'  THEN 1.0 ELSE 0.0 END)      AS prev_refused_share,
    SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Canceled' THEN 1 ELSE 0 END)          AS prev_canceled_count,
    SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Refused' AND DAYS_DECISION >= -365 THEN 1 ELSE 0 END)
                                                                                AS prev_refused_last_12m,
    -MAX(DAYS_DECISION)                                                         AS prev_days_since_last_decision,
    AVG(AMT_CREDIT / NULLIF(AMT_APPLICATION, 0))                                AS prev_avg_given_to_asked,
    AVG(AMT_APPLICATION)                                                        AS prev_avg_amount_asked,
    MAX(AMT_CREDIT)                                                             AS prev_max_credit,
    AVG(CNT_PAYMENT)                                                            AS prev_avg_term_months,
    AVG(RATE_DOWN_PAYMENT)                                                      AS prev_avg_down_payment_rate,
    AVG(CASE WHEN NAME_YIELD_GROUP = 'high' THEN 1.0 ELSE 0.0 END)              AS prev_high_rate_share,
    AVG(CASE WHEN NAME_CONTRACT_TYPE = 'Cash loans' THEN 1.0 ELSE 0.0 END)      AS prev_cash_loan_share
FROM raw.previous_application
GROUP BY SK_ID_CURR;