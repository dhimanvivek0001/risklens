# 02 - Feature summary

- Applicants: **356,255** (307,511 train, 48,744 test)
- Features: **112** (102 numeric, 10 text/categorical)

## History coverage

| History | Share of applicants | Bad rate with | Bad rate without |
| --- | --- | --- | --- |
| bureau history | 85.8% | 7.73% | 10.12% |
| previous application | 95.1% | 8.19% | 5.96% |
| instalment history | 95.3% | 8.19% | 5.98% |
| pos cash history | 94.7% | 8.16% | 6.66% |
| credit card history | 29.1% | 8.67% | 7.84% |

## Top 25 features by stand-alone Gini (train data)

Gini = |2 x AUC - 1| for each feature on its own. 0 = no signal; above about 0.10 is useful for a single credit variable.

| Rank | Feature | Gini | Missing |
| --- | --- | --- | --- |
| 1 | ext_source_mean | 0.433 | 0.1% |
| 2 | ext_source_min | 0.382 | 0.1% |
| 3 | ext_source_max | 0.372 | 0.1% |
| 4 | EXT_SOURCE_3 | 0.359 | 19.5% |
| 5 | EXT_SOURCE_1 | 0.331 | 54.4% |
| 6 | EXT_SOURCE_2 | 0.312 | 0.2% |
| 7 | cc_avg_utilisation_6m | 0.288 | 77.2% |
| 8 | cc_avg_utilisation | 0.257 | 71.2% |
| 9 | bur_card_utilisation | 0.235 | 84.8% |
| 10 | cc_max_utilisation | 0.214 | 71.2% |
| 11 | cc_avg_drawings | 0.214 | 70.9% |
| 12 | bur_active_share | 0.168 | 14.2% |
| 13 | bur_debt_to_credit | 0.167 | 33.7% |
| 14 | age_years | 0.166 | 0.0% |
| 15 | years_employed | 0.165 | 18.1% |
| 16 | cc_max_balance | 0.164 | 70.9% |
| 17 | bur_days_since_last_loan | 0.161 | 14.2% |
| 18 | bur_loans_last_12m | 0.160 | 14.2% |
| 19 | bur_years_since_first_loan | 0.157 | 14.2% |
| 20 | inst_late_share_12m | 0.149 | 29.1% |
| 21 | prev_avg_given_to_asked | 0.146 | 5.2% |
| 22 | employed_to_age_ratio | 0.139 | 18.1% |
| 23 | goods_to_credit | 0.138 | 0.1% |
| 24 | inst_late_share | 0.128 | 4.7% |
| 25 | bur_active_count | 0.121 | 14.2% |

## Missing values

- Features with no missing values: **26**
- Features more than 50% missing: **17** (mostly history features: missing = no history, which is itself information)
