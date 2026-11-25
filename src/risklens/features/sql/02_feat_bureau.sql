-- 02 Features from the credit bureau: loans at OTHER lenders
-- Step 1: summarise bureau_balance (27M monthly rows) to one row per outside loan
-- Step 2: summarise bureau to one row per applicant
-- Grain of output: one row per SK_ID_CURR

CREATE SCHEMA IF NOT EXISTS features;

CREATE OR REPLACE TABLE features.bureau AS
WITH bb AS (
    SELECT
        SK_ID_BUREAU,
        COUNT(*)                                                             AS bb_months,
        MAX(CASE WHEN STATUS IN ('1','2','3','4','5') THEN CAST(STATUS AS INTEGER) ELSE 0 END)
                                                                             AS bb_worst_status,
        AVG(CASE WHEN STATUS IN ('1','2','3','4','5') THEN 1.0 ELSE 0.0 END) AS bb_late_share,
        SUM(CASE WHEN STATUS IN ('1','2','3','4','5') AND MONTHS_BALANCE >= -12 THEN 1 ELSE 0 END)
                                                                             AS bb_late_months_12m
    FROM raw.bureau_balance
    GROUP BY SK_ID_BUREAU
)
SELECT
    b.SK_ID_CURR,
    COUNT(*)                                                             AS bur_loan_count,
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' THEN 1 ELSE 0 END)          AS bur_active_count,
    AVG(CASE WHEN b.CREDIT_ACTIVE = 'Active' THEN 1.0 ELSE 0.0 END)      AS bur_active_share,
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Bad debt' THEN 1 ELSE 0 END)        AS bur_bad_debt_count,
    COUNT(DISTINCT b.CREDIT_TYPE)                                        AS bur_credit_type_count,
    -MIN(b.DAYS_CREDIT) / 365.25                                         AS bur_years_since_first_loan,
    -MAX(b.DAYS_CREDIT)                                                  AS bur_days_since_last_loan,
    SUM(CASE WHEN b.DAYS_CREDIT >= -365 THEN 1 ELSE 0 END)               AS bur_loans_last_12m,
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' THEN b.AMT_CREDIT_SUM_DEBT END) AS bur_active_debt_sum,
    SUM(CASE WHEN b.CREDIT_ACTIVE = 'Active' THEN b.AMT_CREDIT_SUM END)  AS bur_active_credit_sum,
    SUM(b.AMT_CREDIT_SUM_OVERDUE)                                        AS bur_overdue_amount_now,
    MAX(b.CREDIT_DAY_OVERDUE)                                            AS bur_max_days_overdue_now,
    MAX(b.AMT_CREDIT_MAX_OVERDUE)                                        AS bur_max_overdue_amount_ever,
    SUM(b.CNT_CREDIT_PROLONG)                                            AS bur_prolong_count,
    AVG(CASE WHEN b.CREDIT_TYPE = 'Credit card' THEN 1.0 ELSE 0.0 END)   AS bur_credit_card_share,
    SUM(CASE WHEN b.CREDIT_TYPE = 'Credit card' AND b.CREDIT_ACTIVE = 'Active' THEN b.AMT_CREDIT_SUM_DEBT END)
      / NULLIF(SUM(CASE WHEN b.CREDIT_TYPE = 'Credit card' AND b.CREDIT_ACTIVE = 'Active'
                        THEN b.AMT_CREDIT_SUM_LIMIT END), 0)             AS bur_card_utilisation,
    MAX(bb.bb_worst_status)                                              AS bur_worst_status_ever,
    AVG(bb.bb_late_share)                                                AS bur_avg_late_month_share,
    SUM(bb.bb_late_months_12m)                                           AS bur_late_months_12m,
    SUM(bb.bb_months)                                                    AS bur_history_months
FROM raw.bureau b
LEFT JOIN bb USING (SK_ID_BUREAU)
GROUP BY b.SK_ID_CURR;