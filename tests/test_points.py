"""Tests for Phase 3 lesson 9d: points scaling, KS and score bands.
Run:  python -m pytest -q
"""

import math

import numpy as np
import pandas as pd
import pytest

from risklens.models.points import ks_statistic, scaling, score_bands, scorecard_table


def test_scaling_600_is_50_to_1_and_20_points_doubles():
    factor, offset = scaling(600, 50, 20)
    assert factor == pytest.approx(20 / math.log(2))                     # 28.85
    assert offset + factor * math.log(50) == pytest.approx(600)          # odds 50:1 -> 600
    assert offset + factor * math.log(100) == pytest.approx(620)         # double odds -> +20


def test_points_add_up_to_the_score_formula():
    factor, offset = scaling(600, 50, 20)
    coefs = pd.DataFrame({"feature": ["intercept", "a", "b"], "coef": [-2.5, -0.8, -0.5]})
    specs = {"a": {"woe": {"low": -0.6, "high": 0.4}}, "b": {"woe": {"x": 0.3, "y": -0.2}}}
    table, neutral = scorecard_table(coefs, specs, factor, offset)
    pts = dict(zip(table["feature"] + "|" + table["bin"], table["points"]))
    log_odds_good = -(-2.5 - 0.8 * 0.4 - 0.5 * 0.3)                      # customer in bins high + x
    assert pts["a|high"] + pts["b|x"] == pytest.approx(offset + factor * log_odds_good, abs=1)
    assert pts["a|high"] > pts["a|low"]                                  # safer bin = more points


def test_ks_perfect_and_useless():
    y = np.array([1, 1, 0, 0])
    assert ks_statistic([1, 2, 3, 4], y) == pytest.approx(1.0)           # all bads score lowest
    assert ks_statistic([5, 5, 5, 5], y) == pytest.approx(0.0)           # same score for everyone


def test_score_bands_are_ordered():
    score = np.arange(1000)
    y = (score < 100).astype(int)                                        # bads are the lowest scores
    bands = score_bands(score, y)
    assert len(bands) == 10 and bands["customers"].sum() == 1000
    assert bands["bad_rate"].iloc[0] == 1.0 and bands["bad_rate"].iloc[-1] == 0.0