# 01 — EDA: application_train

## Size and target

- Applications: **307,511**
- Columns: **122**
- Bad rate (TARGET=1): **8.07%**
- Break-even bad rate (margin 8%, LGD 60%): **11.76%**

## Top 15 columns by missing share

| Column | Missing |
| --- | --- |
| COMMONAREA_AVG | 69.9% |
| COMMONAREA_MODE | 69.9% |
| COMMONAREA_MEDI | 69.9% |
| NONLIVINGAPARTMENTS_MEDI | 69.4% |
| NONLIVINGAPARTMENTS_MODE | 69.4% |
| NONLIVINGAPARTMENTS_AVG | 69.4% |
| FONDKAPREMONT_MODE | 68.4% |
| LIVINGAPARTMENTS_AVG | 68.4% |
| LIVINGAPARTMENTS_MEDI | 68.4% |
| LIVINGAPARTMENTS_MODE | 68.4% |
| FLOORSMIN_MODE | 67.8% |
| FLOORSMIN_AVG | 67.8% |
| FLOORSMIN_MEDI | 67.8% |
| YEARS_BUILD_AVG | 66.5% |
| YEARS_BUILD_MODE | 66.5% |

Columns with >50% missing: **41**

## Data quality flags

- `DAYS_EMPLOYED = 365243` (placeholder, not a real value): **18.0%** of rows — treat as missing and add a flag feature.

## Key numeric columns

| Column | Mean | Median | Min | Max |
| --- | --- | --- | --- | --- |
| AMT_INCOME_TOTAL | 168,797.919 | 147,150.000 | 25,650.000 | 117,000,000.000 |
| AMT_CREDIT | 599,026.000 | 513,531.000 | 45,000.000 | 4,050,000.000 |
| AMT_ANNUITY | 27,108.574 | 24,903.000 | 1,615.500 | 258,025.500 |
| DAYS_BIRTH | -16,036.995 | -15,750.000 | -25,229.000 | -7,489.000 |
| DAYS_EMPLOYED | 63,815.046 | -1,213.000 | -17,912.000 | 365,243.000 |
| EXT_SOURCE_1 | 0.502 | 0.506 | 0.015 | 0.963 |
| EXT_SOURCE_2 | 0.514 | 0.566 | 0.000 | 0.855 |
| EXT_SOURCE_3 | 0.511 | 0.535 | 0.001 | 0.896 |

## Bad rate by EXT_SOURCE_2 quintile

| Band | Applications | Bad rate |
| --- | --- | --- |
| -0.00 – 0.34 | 61,371 | 15.21% |
| 0.34 – 0.51 | 61,371 | 9.16% |
| 0.51 – 0.61 | 61,371 | 7.04% |
| 0.61 – 0.68 | 61,377 | 5.37% |
| 0.68 – 0.85 | 61,361 | 3.59% |

## Baseline policy economics

| Policy | Approval rate | Bad rate (approved) | Bads declined | Profit per 10k apps* |
| --- | --- | --- | --- | --- |
| Approve everyone | 100.0% | 8.07% | 0.0% | 173,024,946 |
| Rule-based baseline | 61.2% | 6.68% | 49.4% | 103,718,034 |

*In the dataset's own currency units (Home Credit does not state the currency). Compare policies with each other, not as real euros.

Business constraint: approval rate ≥ 70%. This is the number every model in later phases has to beat.
