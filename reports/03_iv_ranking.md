# 03 - Information Value ranking

## Train / valid / test split

| Split | Applications | Bad rate |
| --- | --- | --- |
| train | 184,507 | 8.07% |
| valid | 61,502 | 8.07% |
| test | 61,502 | 8.07% |

## How many features in each IV band

| Strength | Features |
| --- | --- |
| suspicious - check for leakage | 1 |
| strong | 4 |
| medium | 3 |
| weak | 59 |
| useless | 44 |

## All features by IV (fitted on train only)

| Rank | Feature | IV | Strength | Bins |
| --- | --- | --- | --- | --- |
| 1 | ext_source_mean | 0.616 | suspicious - check for leakage | 11 |
| 2 | ext_source_min | 0.470 | strong | 11 |
| 3 | ext_source_max | 0.447 | strong | 11 |
| 4 | EXT_SOURCE_3 | 0.345 | strong | 11 |
| 5 | EXT_SOURCE_2 | 0.308 | strong | 11 |
| 6 | EXT_SOURCE_1 | 0.148 | medium | 11 |
| 7 | credit_to_annuity | 0.138 | medium | 11 |
| 8 | years_employed | 0.113 | medium | 11 |
| 9 | bur_active_share | 0.094 | weak | 9 |
| 10 | employed_to_age_ratio | 0.092 | weak | 11 |
| 11 | bur_loans_last_12m | 0.092 | weak | 6 |
| 12 | AMT_GOODS_PRICE | 0.087 | weak | 11 |
| 13 | bur_days_since_last_loan | 0.084 | weak | 11 |
| 14 | age_years | 0.083 | weak | 10 |
| 15 | bur_years_since_first_loan | 0.082 | weak | 11 |
| 16 | cc_avg_utilisation_6m | 0.078 | weak | 8 |
| 17 | goods_to_credit | 0.074 | weak | 9 |
| 18 | prev_refused_share | 0.073 | weak | 6 |
| 19 | cc_avg_utilisation | 0.073 | weak | 9 |
| 20 | prev_avg_given_to_asked | 0.071 | weak | 11 |
| 21 | inst_late_share_12m | 0.071 | weak | 5 |
| 22 | inst_late_share | 0.063 | weak | 8 |
| 23 | OCCUPATION_TYPE | 0.062 | weak | 8 |
| 24 | prev_refused_count | 0.058 | weak | 5 |
| 25 | NAME_INCOME_TYPE | 0.058 | weak | 5 |
| 26 | bur_active_count | 0.058 | weak | 7 |
| 27 | cc_avg_drawings | 0.057 | weak | 9 |
| 28 | bur_debt_to_credit | 0.057 | weak | 11 |
| 29 | inst_paid_to_due_ratio | 0.055 | weak | 7 |
| 30 | NAME_EDUCATION_TYPE | 0.052 | weak | 3 |
| 31 | inst_underpaid_share | 0.052 | weak | 7 |
| 32 | inst_avg_days_late | 0.052 | weak | 8 |
| 33 | cc_max_utilisation | 0.051 | weak | 9 |
| 34 | prev_refused_last_12m | 0.049 | weak | 4 |
| 35 | REGION_RATING_CLIENT_W_CITY | 0.048 | weak | 3 |
| 36 | days_since_phone_change | 0.045 | weak | 11 |
| 37 | ORGANIZATION_TYPE | 0.045 | weak | 4 |
| 38 | bur_card_utilisation | 0.044 | weak | 10 |
| 39 | AMT_CREDIT | 0.044 | weak | 10 |
| 40 | inst_max_days_late | 0.040 | weak | 11 |
| 41 | years_since_id_change | 0.040 | weak | 10 |
| 42 | pos_loan_count | 0.036 | weak | 7 |
| 43 | cc_max_balance | 0.035 | weak | 9 |
| 44 | REGION_POPULATION_RELATIVE | 0.035 | weak | 10 |
| 45 | inst_underpaid_amount | 0.034 | weak | 7 |
| 46 | FLAG_EMPLOYED_PLACEHOLDER | 0.034 | weak | 2 |
| 47 | pos_months | 0.032 | weak | 11 |
| 48 | bur_credit_card_share | 0.032 | weak | 9 |
| 49 | cc_avg_paid_to_minimum | 0.029 | weak | 11 |
| 50 | years_since_registration | 0.027 | weak | 10 |
| 51 | inst_loan_count | 0.027 | weak | 7 |
| 52 | prev_high_rate_share | 0.025 | weak | 8 |
| 53 | prev_approved_count | 0.025 | weak | 8 |
| 54 | pos_dpd_month_share | 0.025 | weak | 4 |
| 55 | prev_avg_term_months | 0.025 | weak | 11 |
| 56 | OWN_CAR_AGE | 0.025 | weak | 11 |
| 57 | AMT_ANNUITY | 0.025 | weak | 11 |
| 58 | bur_overdue_amount_now | 0.024 | weak | 3 |
| 59 | bur_max_days_overdue_now | 0.024 | weak | 3 |
| 60 | pos_completed_share | 0.022 | weak | 7 |
| 61 | bur_max_overdue_amount_ever | 0.022 | weak | 6 |
| 62 | pos_active_share | 0.022 | weak | 7 |
| 63 | documents_provided | 0.022 | weak | 4 |
| 64 | pos_max_dpd | 0.022 | weak | 4 |
| 65 | cc_months | 0.021 | weak | 11 |
| 66 | bur_debt_to_income | 0.021 | weak | 11 |
| 67 | NAME_FAMILY_STATUS | 0.020 | weak | 6 |
| 68 | AMT_REQ_CREDIT_BUREAU_YEAR | 0.020 | useless | 7 |
| 69 | bur_active_debt_sum | 0.020 | useless | 11 |
| 70 | pos_dpd_months_12m | 0.019 | useless | 3 |
| 71 | pos_remaining_instalments | 0.019 | useless | 7 |
| 72 | prev_avg_down_payment_rate | 0.018 | useless | 10 |
| 73 | prev_avg_amount_asked | 0.017 | useless | 11 |
| 74 | bur_loan_count | 0.016 | useless | 10 |
| 75 | prev_max_credit | 0.016 | useless | 11 |
| 76 | DEF_30_CNT_SOCIAL_CIRCLE | 0.016 | useless | 9 |
| 77 | DEF_60_CNT_SOCIAL_CIRCLE | 0.015 | useless | 9 |
| 78 | bur_avg_late_month_share | 0.015 | useless | 6 |
| 79 | bur_credit_type_count | 0.015 | useless | 7 |
| 80 | inst_payment_count | 0.015 | useless | 11 |
| 81 | NAME_CONTRACT_TYPE | 0.014 | useless | 2 |
| 82 | bur_prolong_count | 0.014 | useless | 9 |
| 83 | bur_bad_debt_count | 0.014 | useless | 3 |
| 84 | prev_app_count | 0.013 | useless | 10 |
| 85 | bur_late_months_12m | 0.013 | useless | 4 |
| 86 | has_bureau_history | 0.013 | useless | 2 |
| 87 | prev_days_since_last_decision | 0.013 | useless | 11 |
| 88 | ext_source_missing_count | 0.012 | useless | 4 |
| 89 | bur_history_months | 0.012 | useless | 11 |
| 90 | inst_late_30_share | 0.011 | useless | 3 |
| 91 | AMT_INCOME_TOTAL | 0.011 | useless | 10 |
| 92 | credit_to_income | 0.011 | useless | 10 |
| 93 | prev_cash_loan_share | 0.010 | useless | 8 |
| 94 | prev_canceled_count | 0.010 | useless | 6 |
| 95 | NAME_HOUSING_TYPE | 0.009 | useless | 2 |
| 96 | cc_max_dpd | 0.009 | useless | 4 |
| 97 | bur_worst_status_ever | 0.008 | useless | 7 |
| 98 | FLAG_OWN_CAR | 0.007 | useless | 2 |
| 99 | inst_avg_days_early | 0.007 | useless | 11 |
| 100 | annuity_to_income | 0.007 | useless | 11 |
| 101 | has_previous_application | 0.006 | useless | 2 |
| 102 | has_instalment_history | 0.006 | useless | 2 |
| 103 | CNT_CHILDREN | 0.005 | useless | 4 |
| 104 | cc_dpd_month_share | 0.005 | useless | 4 |
| 105 | bur_active_credit_sum | 0.004 | useless | 11 |
| 106 | CNT_FAM_MEMBERS | 0.004 | useless | 5 |
| 107 | income_per_person | 0.004 | useless | 11 |
| 108 | has_pos_cash_history | 0.003 | useless | 2 |
| 109 | cc_card_count | 0.003 | useless | 5 |
| 110 | has_credit_card_history | 0.002 | useless | 2 |
| 111 | FLAG_OWN_REALTY | 0.000 | useless | 2 |

## Example WoE table: EXT_SOURCE_2

| Bin | Customers | Bad rate | WoE | IV part |
| --- | --- | --- | --- | --- |
| 00: (-inf, 0.2151] | 18,413 | 18.23% | -0.931 | 0.1271 |
| 01: (0.2151, 0.34] | 18,407 | 12.20% | -0.458 | 0.0254 |
| 02: (0.34, 0.4405] | 18,410 | 9.90% | -0.224 | 0.0055 |
| 03: (0.4405, 0.5125] | 18,411 | 8.39% | -0.042 | 0.0002 |
| 04: (0.5125, 0.5664] | 18,410 | 7.60% | +0.066 | 0.0004 |
| 05: (0.5664, 0.6085] | 18,409 | 6.62% | +0.215 | 0.0042 |
| 06: (0.6085, 0.6463] | 18,411 | 5.93% | +0.331 | 0.0095 |
| 07: (0.6463, 0.6824] | 18,409 | 4.76% | +0.564 | 0.0251 |
| 08: (0.6824, 0.7224] | 18,411 | 4.28% | +0.675 | 0.0344 |
| 09: (0.7224, inf] | 18,409 | 2.87% | +1.089 | 0.0762 |
| Missing | 407 | 6.14% | +0.276 | 0.0002 |
