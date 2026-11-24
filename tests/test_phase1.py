"""Tests for Phase 1: economics maths, loading, and the EDA report.

Uses a small synthetic application file so tests run without the Kaggle data.
Run:  pytest -q
"""

import numpy as np
import pandas as pd
import pytest

from risklens import load_settings
from risklens.data.load import load_raw
from risklens.economics.profit_matrix import Economics, policy_profit
from risklens.eda.profile_application import baseline_approve, build_report


def test_break_even_bad_rate():
    econ = Economics(net_margin=0.08, lgd=0.60)
    assert econ.break_even_bad_rate == pytest.approx(0.08 / 0.68)


def test_policy_profit_hand_calculated():
    econ = Economics(net_margin=0.10, lgd=0.50)
    approve = [1, 1, 1, 0]
    target = [0, 0, 1, 1]
    amount = [1000, 2000, 1000, 5000]
    # +0.10*(1000+2000) - 0.50*1000 = 300 - 500 = -200
    out = policy_profit(approve, target, amount, econ)
    assert out["total_profit"] == pytest.approx(-200)
    assert out["approval_rate"] == pytest.approx(0.75)
    assert out["bad_rate_approved"] == pytest.approx(1 / 3)
    assert out["bads_declined_share"] == pytest.approx(0.5)


@pytest.fixture
def synthetic_apps() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 2_000
    ext2 = rng.uniform(0, 1, n)
    # Lower external score -> higher chance of being bad (like the real data)
    target = (rng.uniform(0, 1, n) < 0.25 - 0.2 * ext2).astype(int)
    days_employed = rng.integers(-15_000, -100, n)
    days_employed[:100] = 365243  # the known placeholder value
    return pd.DataFrame(
        {
            "SK_ID_CURR": np.arange(n),
            "TARGET": target,
            "AMT_INCOME_TOTAL": rng.uniform(50_000, 300_000, n),
            "AMT_CREDIT": rng.uniform(100_000, 1_200_000, n),
            "AMT_ANNUITY": rng.uniform(5_000, 60_000, n),
            "DAYS_BIRTH": rng.integers(-25_000, -7_000, n),
            "DAYS_EMPLOYED": days_employed,
            "EXT_SOURCE_1": np.where(rng.uniform(0, 1, n) < 0.55, np.nan, rng.uniform(0, 1, n)),
            "EXT_SOURCE_2": ext2,
            "EXT_SOURCE_3": rng.uniform(0, 1, n),
        }
    )


def test_baseline_declines_low_scores(synthetic_apps):
    rules = load_settings()["baseline_rules"]
    approve = baseline_approve(synthetic_apps, rules)
    low = synthetic_apps["EXT_SOURCE_2"] < rules["ext_source_2_min"]
    assert not approve[low].any()


def test_load_and_report_end_to_end(tmp_path, synthetic_apps):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    synthetic_apps.to_csv(raw_dir / "application_train.csv", index=False)
    db_file = tmp_path / "test.duckdb"

    counts = load_raw(raw_dir=raw_dir, db_file=db_file)
    assert counts == {"application_train": len(synthetic_apps)}

    report = build_report(synthetic_apps, load_settings())
    assert "Baseline policy economics" in report
    assert "365243" in report
    assert "Bad rate by EXT_SOURCE_2 quintile" in report
