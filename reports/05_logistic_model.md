# 05 - Logistic regression scorecard model

## How well it ranks customers (Gini)

| Data | Customers | Gini |
| --- | --- | --- |
| train | 184,507 | 0.500 |
| valid | 61,502 | 0.492 |

Train - valid gap: **+0.008** (OK, no sign of overfitting)

## Coefficients

Every feature coefficient must be negative (higher WoE = safer = lower chance of default).

| Feature | Coefficient | Std error | p-value |
| --- | --- | --- | --- |
| intercept | -2.4348 | 0.0095 | 0 |
| ext_source_mean | -0.7114 | 0.0155 | 0 |
| EXT_SOURCE_3 | -0.2368 | 0.0199 | 1.2e-32 |
| EXT_SOURCE_1 | -0.1372 | 0.0277 | 7.3e-07 |
| years_employed | -0.4365 | 0.0292 | 1.4e-50 |
| bur_active_share | -0.2126 | 0.0363 | 4.6e-09 |
| bur_loans_last_12m | -0.1498 | 0.0331 | 6.2e-06 |
| bur_years_since_first_loan | -0.1768 | 0.0371 | 1.9e-06 |
| goods_to_credit | -0.6689 | 0.0318 | 1.6e-98 |
| prev_refused_share | -0.4595 | 0.0324 | 9.6e-46 |
| inst_late_share_12m | -0.4380 | 0.0374 | 1.2e-31 |
| prev_avg_given_to_asked | -0.4710 | 0.0339 | 8.4e-44 |
| inst_late_share | -0.3962 | 0.0417 | 2.2e-21 |
| OCCUPATION_TYPE | -0.4872 | 0.0372 | 4.2e-39 |
| cc_avg_utilisation | -0.5774 | 0.0357 | 8.2e-59 |

## Removed during cleaning

| Feature | Reason |
| --- | --- |
| age_years | wrong sign (coef +0.116) |
