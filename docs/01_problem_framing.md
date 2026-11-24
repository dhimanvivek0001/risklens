# 01 — Problem Framing

**Project:** RiskLens — credit and fraud decisioning engine
**Phase:** 1 of 7 (Problem framing)
**Owner:** Vivek
**Status:** Draft v1

---

## 1. Business problem

Small lenders, BNPL apps and credit unions approve loans with simple rules ("income > X, no defaults"). This causes:

- **Credit losses** from approving people who later default
- **Lost revenue** from declining good customers
- **No explainability**, so they can't tell a declined customer why, which regulators expect

Banks solve this with credit risk teams (PD models, scorecards, IFRS 9). RiskLens offers the same as an API.

## 2. Decision being supported

> For each loan application: **approve or decline**, and later, **at what limit / price**.

The model only matters if it changes this decision for the better.

## 3. Target definition

| Item | Definition |
| --- | --- |
| Dataset | Home Credit Default Risk (Kaggle) |
| Target (as provided) | `TARGET = 1` if the client had payment difficulties (late payment beyond the lender's threshold on at least one of the first installments); `0` otherwise |
| Why we use it as given | We do not have raw repayment schedules to rebuild a 90+ days-past-due flag, so we document the definition honestly instead of inventing one |
| Observation point | Application date |
| Unit of analysis | One application (`SK_ID_CURR`) |

**Note for interviews:** banks usually define default as 90+ days past due within 12 months (aligned to Basel / IFRS 9). Our target is a proxy for that; this is a known limitation, recorded in the model card.

## 4. Economics: the profit matrix

Accuracy is not the goal. The goal is **expected profit per application**.

| | Actually good (TARGET=0) | Actually bad (TARGET=1) |
| --- | --- | --- |
| **Approve** | + margin × loan amount | − LGD × loan amount |
| **Decline** | 0 (lost opportunity is captured by comparing policies) | 0 (loss avoided) |

Default assumptions (in `config/settings.yaml`, change them to run scenarios):

| Parameter | Value | Meaning |
| --- | --- | --- |
| `net_margin` | 0.08 | Net interest + fees earned on a good loan, after funding cost |
| `lgd` | 0.60 | Loss given default: share of the loan lost if the customer defaults |
| `min_approval_rate` | 0.70 | Business constraint: approve at least 70% of applicants |

**Break-even bad rate** for an approved group = margin / (margin + LGD) = 0.08 / 0.68 ≈ **11.8%**.
If a segment's predicted bad rate is above ~11.8%, approving it loses money on average.

## 5. Success metrics

| Type | Metric | Target |
| --- | --- | --- |
| Business | Expected profit per 10,000 applications vs current rule-based policy | Positive uplift (in dataset currency units; Home Credit does not state the currency) |
| Business | Approval rate | ≥ 70% |
| Model | AUC (ROC) | ≥ 0.75 (Home Credit benchmarks sit around 0.75–0.80) |
| Model | Gini (= 2·AUC − 1) | ≥ 0.50 — banks report Gini |
| Model | KS statistic | Report it — standard in credit risk |
| Stability | PSI between train and out-of-time sample | < 0.10 |
| Fairness | Approval-rate gap across gender / age bands | Report and explain |

## 6. Baseline to beat

A simple rule set similar to what a small lender might use:

- Decline if `EXT_SOURCE_2` (external bureau score) < 0.3
- Decline if credit / income ratio > 5
- Approve otherwise

Every model is compared against this baseline on profit, not only AUC.

## 7. Scope

**In scope (v1):** application-level PD model, scorecard + ML challenger, profit-based cut-off, explainability, IFRS 9 ECL, decision API, monitoring.
**Later:** transaction fraud model (IEEE-CIS), limit and pricing optimisation.
**Out of scope:** real customer data, regulatory approval.

## 8. Risks and assumptions

| Risk | Mitigation |
| --- | --- |
| Target is a proxy, not true 90+ DPD default | Documented; sensitivity on LGD and margin |
| Data leakage from future information | Only use features known at application time; check every bureau feature |
| Bias against protected groups | Exclude gender from features; measure outcome gaps with Fairlearn |
| Economics are assumptions | All parameters in config; scenario table in final report |

## 9. Data inventory

| Table | Rows (approx.) | Grain | Use |
| --- | --- | --- | --- |
| application_train | 307k | application | Target + main features |
| application_test | 49k | application | Scoring demo (no target) |
| bureau | 1.7M | prior credit at other lenders | Aggregated features |
| bureau_balance | 27M | month × bureau credit | Delinquency history |
| previous_application | 1.7M | prior Home Credit application | Behaviour features |
| installments_payments | 13.6M | installment | Payment behaviour |
| POS_CASH_balance / credit_card_balance | 10M / 3.8M | month | Usage behaviour |

## 10. Next phase

Phase 2 — Feature engineering: aggregate bureau and payment history into 150+ application-level features (pandas/DuckDB first, then PySpark on Databricks).

## 11. Phase 1 results (real data)

- Warehouse: 9 tables, 58.8M rows loaded into DuckDB (largest: bureau_balance, 27.3M).
- Bad rate 8.07% vs break-even 11.76%, so the portfolio is profitable on average.
- Rule-based baseline: 61.2% approval, 103.7M profit per 10k apps. That is LOWER than approve-all (173.0M), and it breaks the 70% approval constraint.
- Lowest EXT_SOURCE_2 quintile has a 15.21% bad rate (above break-even); the other quintiles are 3.6-9.2%.
- DAYS_EMPLOYED = 365243 placeholder on 18.0% of rows; flag it in Phase 2.
- New benchmark to beat: approve-all, 173.0M per 10k applications.
