# RiskLens — Credit & Fraud Decisioning Engine

> Bank-grade credit and fraud decisions as an API, for lenders, BNPL apps and fintechs that can't afford a risk team.

**Mirrors the work of:** credit risk modelling teams at JPMorgan, Citi and BofA; fraud scoring at Mastercard and Visa; model validation at the Big 4.

## Status

| Phase | What | Status |
| --- | --- | --- |
| 1 | Problem framing, profit matrix, data load, EDA, baseline policy | ✅ Code ready — run on real data |
| 2 | Feature engineering (bureau, payments, behaviour) — pandas/DuckDB → PySpark on Databricks | ⏳ |
| 3–4 | WoE scorecard (champion) + XGBoost (challenger), calibration, profit-based cut-off | ⏳ |
| 5 | IFRS 9 staging, expected credit loss, macro stress test | ⏳ |
| 6 | FastAPI decision service, MLflow registry, drift monitoring | ⏳ |
| 7 | Model card, validation report, fairness, LLM decline letters | ⏳ |

## Project structure

```
risklens/
├── config/settings.yaml          # economics + rule thresholds (change here, not in code)
├── docs/01_problem_framing.md    # target, profit matrix, success metrics, risks
├── src/risklens/
│   ├── data/download.py          # Kaggle API download
│   ├── data/load.py              # CSV -> DuckDB raw schema
│   ├── economics/profit_matrix.py# decisions -> money
│   └── eda/profile_application.py# EDA + baseline policy report
├── tests/test_phase1.py          # runs without Kaggle data
├── reports/                      # generated reports (01_eda_application.md)
└── data/                         # git-ignored
```

## Setup (Windows PowerShell)

```powershell
cd risklens
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
pytest -q                          # 4 tests should pass
```

## Phase 1 — run it

1. Accept the competition rules: https://www.kaggle.com/competitions/home-credit-default-risk/rules
2. Kaggle → Settings → API → **Create New Token** → save to `C:\Users\<you>\.kaggle\kaggle.json`
3. Run:

```powershell
python -m risklens.data.download              # ~700 MB zip, 10 CSVs
python -m risklens.data.load                  # loads all tables into data/processed/risklens.duckdb
python -m risklens.eda.profile_application    # writes reports/01_eda_application.md
```

4. Open `reports/01_eda_application.md` and fill section 6 of `docs/01_problem_framing.md` with the real baseline numbers.

## Key idea

Models are judged on **expected profit at a given approval rate**, not accuracy:

- Good loan approved → + net margin × loan amount
- Bad loan approved → − LGD × loan amount
- Break-even bad rate = margin / (margin + LGD) ≈ 11.8% with default settings
