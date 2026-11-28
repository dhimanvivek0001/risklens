"""Tests for Phase 2 feature engineering.

Builds a tiny fake warehouse with the real Home Credit column names,
runs every SQL file, and checks values that were worked out by hand.
Run:  python -m pytest -q
"""

import duckdb
import numpy as np
import pandas as pd
import pytest

from risklens.features.build import (
    FINAL_TABLE, build_report, quality_checks, run_sql_files, univariate_gini,
)


def _applications(ids, with_target=True):
    n = len(ids)
    df = pd.DataFrame({
        "SK_ID_CURR": ids,
        "NAME_CONTRACT_TYPE": "Cash loans", "CODE_GENDER": "F",
        "FLAG_OWN_CAR": "N", "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0, "CNT_FAM_MEMBERS": 2.0,
        "AMT_INCOME_TOTAL": 100_000.0, "AMT_CREDIT": 300_000.0,
        "AMT_ANNUITY": 15_000.0, "AMT_GOODS_PRICE": 270_000.0,
        "NAME_INCOME_TYPE": "Working", "NAME_EDUCATION_TYPE": "Higher education",
        "NAME_FAMILY_STATUS": "Married", "NAME_HOUSING_TYPE": "House / apartment",
        "OCCUPATION_TYPE": "Laborers", "ORGANIZATION_TYPE": "Business Entity Type 3",
        "REGION_POPULATION_RELATIVE": 0.02, "REGION_RATING_CLIENT_W_CITY": 2,
        "OWN_CAR_AGE": np.nan,
        "EXT_SOURCE_1": np.nan, "EXT_SOURCE_2": 0.6, "EXT_SOURCE_3": 0.4,
        "DAYS_BIRTH": -36525, "DAYS_EMPLOYED": -3652, "DAYS_ID_PUBLISH": -1000,
        "DAYS_REGISTRATION": -2000.0, "DAYS_LAST_PHONE_CHANGE": -500.0,
        "AMT_REQ_CREDIT_BUREAU_YEAR": 1.0,
        "DEF_30_CNT_SOCIAL_CIRCLE": 0.0, "DEF_60_CNT_SOCIAL_CIRCLE": 0.0,
    }, index=range(n))
    for k in range(2, 22):
        df[f"FLAG_DOCUMENT_{k}"] = 0
    df["FLAG_DOCUMENT_3"] = 1
    if with_target:
        df.insert(1, "TARGET", [i % 2 for i in range(n)])
    return df


@pytest.fixture
def con():
    c = duckdb.connect()  # in-memory database
    c.execute("CREATE SCHEMA raw").fetchall()

    train = _applications([1, 2, 3, 4])
    train.loc[train.SK_ID_CURR == 2, "DAYS_EMPLOYED"] = 365243       # pensioner placeholder
    test = _applications([9], with_target=False)

    bureau = pd.DataFrame({
        "SK_ID_CURR":   [1, 1, 2],
        "SK_ID_BUREAU": [10, 11, 12],
        "CREDIT_ACTIVE": ["Active", "Closed", "Active"],
        "CREDIT_TYPE": ["Consumer credit", "Credit card", "Credit card"],
        "DAYS_CREDIT": [-100, -2000, -400],
        "CREDIT_DAY_OVERDUE": [0, 0, 5],
        "AMT_CREDIT_SUM": [50_000.0, 10_000.0, 20_000.0],
        "AMT_CREDIT_SUM_DEBT": [30_000.0, 0.0, 15_000.0],
        "AMT_CREDIT_SUM_LIMIT": [0.0, 10_000.0, 20_000.0],
        "AMT_CREDIT_SUM_OVERDUE": [0.0, 0.0, 500.0],
        "AMT_CREDIT_MAX_OVERDUE": [0.0, np.nan, 900.0],
        "CNT_CREDIT_PROLONG": [0, 0, 1],
    })
    bureau_balance = pd.DataFrame({
        "SK_ID_BUREAU":   [10, 10, 10, 10, 11, 12],
        "MONTHS_BALANCE": [0, -1, -2, -20, -30, -3],
        "STATUS":         ["0", "1", "X", "3", "C", "2"],
    })
    previous = pd.DataFrame({
        "SK_ID_PREV": [100, 101, 102], "SK_ID_CURR": [1, 1, 3],
        "NAME_CONTRACT_STATUS": ["Approved", "Refused", "Refused"],
        "NAME_CONTRACT_TYPE": ["Cash loans", "Consumer loans", "Cash loans"],
        "NAME_YIELD_GROUP": ["high", "low_normal", "high"],
        "DAYS_DECISION": [-800, -200, -50],
        "AMT_APPLICATION": [100_000.0, 50_000.0, 80_000.0],
        "AMT_CREDIT": [90_000.0, 0.0, 0.0],
        "CNT_PAYMENT": [12.0, np.nan, 24.0],
        "RATE_DOWN_PAYMENT": [0.1, np.nan, 0.0],
    })
    # applicant 1: 4 payments, 2 late (by 5 and 40 days), 1 underpaid by 200
    installments = pd.DataFrame({
        "SK_ID_PREV": [100, 100, 100, 100], "SK_ID_CURR": [1, 1, 1, 1],
        "DAYS_INSTALMENT":    [-400, -370, -100, -70],
        "DAYS_ENTRY_PAYMENT": [-405, -330, -95, -70],
        "AMT_INSTALMENT": [1000.0, 1000.0, 1000.0, 1000.0],
        "AMT_PAYMENT":    [1000.0, 1000.0, 800.0, 1000.0],
    })
    pos = pd.DataFrame({
        "SK_ID_PREV": [100, 100, 100], "SK_ID_CURR": [1, 1, 1],
        "MONTHS_BALANCE": [-3, -2, -1],
        "CNT_INSTALMENT_FUTURE": [10.0, 9.0, 8.0],
        "NAME_CONTRACT_STATUS": ["Active", "Active", "Active"],
        "SK_DPD_DEF": [0, 3, 0],
    })
    cc = pd.DataFrame({
        "SK_ID_PREV": [200, 200], "SK_ID_CURR": [4, 4],
        "MONTHS_BALANCE": [-2, -1],
        "AMT_BALANCE": [5000.0, 10_000.0], "AMT_CREDIT_LIMIT_ACTUAL": [10_000.0, 10_000.0],
        "SK_DPD_DEF": [0, 0], "AMT_PAYMENT_CURRENT": [500.0, 1000.0],
        "AMT_INST_MIN_REGULARITY": [500.0, 500.0], "AMT_DRAWINGS_CURRENT": [0.0, 2000.0],
    })
    for name, df in {
        "application_train": train, "application_test": test, "bureau": bureau,
        "bureau_balance": bureau_balance, "previous_application": previous,
        "installments_payments": installments, "pos_cash_balance": pos,
        "credit_card_balance": cc,
    }.items():
        c.register("tmp", df)
        c.execute(f"CREATE TABLE raw.{name} AS SELECT * FROM tmp").fetchall()
        c.unregister("tmp")

    run_sql_files(c)
    yield c
    c.close()


def _row(con, sk_id):
    return con.execute(f"SELECT * FROM {FINAL_TABLE} WHERE SK_ID_CURR = {sk_id}").df().iloc[0]


def test_one_row_per_applicant(con):
    counts = quality_checks(con)
    assert counts == {"rows": 5, "distinct_ids": 5}


def test_application_cleaning_and_ratios(con):
    r1, r2 = _row(con, 1), _row(con, 2)
    assert r1["age_years"] == pytest.approx(100.0)
    assert r1["credit_to_income"] == pytest.approx(3.0)
    assert r1["ext_source_mean"] == pytest.approx(0.5)           # (0.6 + 0.4) / 2, missing ignored
    assert r1["ext_source_missing_count"] == 1
    assert r1["documents_provided"] == 1
    assert r2["FLAG_EMPLOYED_PLACEHOLDER"] == 1
    assert pd.isna(r2["years_employed"])                          # 365243 became missing


def test_bureau_features(con):
    r1 = _row(con, 1)
    assert r1["bur_loan_count"] == 2
    assert r1["bur_active_count"] == 1
    assert r1["bur_active_debt_sum"] == pytest.approx(30_000)
    assert r1["bur_debt_to_credit"] == pytest.approx(30_000 / 50_000)
    assert r1["bur_worst_status_ever"] == 3                       # status '3' on loan 10
    assert r1["bur_late_months_12m"] == 1                         # only month -1 is late within 12m
    r2 = _row(con, 2)
    assert r2["bur_card_utilisation"] == pytest.approx(15_000 / 20_000)


def test_previous_and_instalment_features(con):
    r1 = _row(con, 1)
    assert r1["prev_app_count"] == 2
    assert r1["prev_refused_share"] == pytest.approx(0.5)
    assert r1["prev_refused_last_12m"] == 1
    assert r1["inst_late_share"] == pytest.approx(0.5)            # 2 of 4 payments late
    assert r1["inst_late_30_share"] == pytest.approx(0.25)        # 1 of 4 more than 30 days late
    assert r1["inst_max_days_late"] == 40
    assert r1["inst_underpaid_share"] == pytest.approx(0.25)
    assert r1["inst_underpaid_amount"] == pytest.approx(200)


def test_pos_and_credit_card_features(con):
    r1 = _row(con, 1)
    assert r1["pos_remaining_instalments"] == 8                   # latest month only
    assert r1["pos_dpd_months_12m"] == 1
    r4 = _row(con, 4)
    assert r4["cc_avg_utilisation"] == pytest.approx(0.75)        # (0.5 + 1.0) / 2
    assert r4["cc_max_utilisation"] == pytest.approx(1.0)
    assert r4["cc_avg_paid_to_minimum"] == pytest.approx(1.5)     # (1 + 2) / 2


def test_history_flags(con):
    r3, r9 = _row(con, 3), _row(con, 9)
    assert r3["has_bureau_history"] == 0 and r3["has_previous_application"] == 1
    assert r9["has_bureau_history"] == 0 and pd.isna(r9["TARGET"])


def test_univariate_gini_perfect_and_none():
    y = pd.Series([0, 0, 1, 1])
    assert univariate_gini(pd.Series([1, 2, 3, 4]), y) == pytest.approx(1.0)
    assert univariate_gini(pd.Series([4, 3, 2, 1]), y) == pytest.approx(1.0)   # direction does not matter
    assert np.isnan(univariate_gini(pd.Series([5, 5, 5, 5]), y))              # one value = no signal


def test_report_builds(con):
    df = con.execute(f"SELECT * FROM {FINAL_TABLE}").df()
    report = build_report(df)
    assert "Top 25 features" in report and "History coverage" in report