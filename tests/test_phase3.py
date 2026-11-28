"""Tests for Phase 3: WoE binning and the train/valid/test split.
Run:  python -m pytest -q
"""

import math

import numpy as np
import pandas as pd
import pytest

from risklens.models.iv_report import make_split
from risklens.models.woe import MISSING, OTHER, fit_feature, iv_strength, transform


def test_woe_and_iv_by_hand():
    # bin A: 3 goods, 1 bad      bin B: 1 good, 3 bads
    x = pd.Series(["A", "A", "A", "A", "B", "B", "B", "B"])
    y = pd.Series([0, 0, 0, 1, 0, 1, 1, 1])
    spec = fit_feature(x, y)
    # with smoothing 0.5: share_good A = 3.5/5 = 0.7, share_bad A = 1.5/5 = 0.3
    assert spec["woe"]["A"] == pytest.approx(math.log(0.7 / 0.3))
    assert spec["woe"]["B"] == pytest.approx(math.log(0.3 / 0.7))
    assert spec["iv"] == pytest.approx(2 * 0.4 * math.log(0.7 / 0.3))


def test_numeric_bins_missing_and_unseen():
    x = pd.Series([1.0, 2, 3, 4, 5, 6, 7, 8, np.nan, np.nan])
    y = pd.Series([1, 1, 0, 0, 0, 0, 0, 0, 1, 0])
    spec = fit_feature(x, y, max_bins=2)
    assert spec["edges"] == [-np.inf, 4.5, np.inf]          # median splits 1-4 from 5-8
    assert MISSING in spec["woe"]                            # missing gets its own bin
    woe = transform(pd.Series([2.0, 7.0, np.nan]), spec)
    assert woe[0] < 0 < woe[1]                               # low values are riskier here
    cat = fit_feature(pd.Series(["a"] * 30 + ["b"]), pd.Series([0, 1] * 15 + [1]))
    assert OTHER in cat["woe"] and "b" not in cat["woe"]     # "b" is under 5%, so it goes into Other
    no_missing = fit_feature(pd.Series([1.0, 2, 3, 4]), pd.Series([0, 1, 0, 1]))
    assert transform(pd.Series([np.nan]), no_missing)[0] == 0.0   # a bin never seen in train = average


def test_split_is_stratified_and_repeatable():
    target = pd.Series([0] * 900 + [1] * 100)
    split = make_split(target, seed=42)
    assert (split == make_split(target, seed=42)).all()      # same seed, same split
    assert split.value_counts().to_dict() == {"train": 600, "valid": 200, "test": 200}
    assert target[split == "valid"].mean() == pytest.approx(0.10)


def test_iv_strength_bands():
    assert [iv_strength(v) for v in (0.01, 0.05, 0.2, 0.4, 0.8)] == [
        "useless", "weak", "medium", "strong", "suspicious - check for leakage"]