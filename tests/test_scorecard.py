"""Tests for Phase 3 lesson 9b: coarse classing and feature selection.
Run:  python -m pytest -q
"""

import numpy as np
import pandas as pd

from risklens.models.scorecard import coarse_edges, merge_bins, select_features


def test_merge_bins_adds_counts_and_removes_a_cut():
    edges, counts, bads = merge_bins([-np.inf, 1, 2, np.inf], [10, 20, 30], [1, 2, 3], 1)
    assert edges == [-np.inf, 1, np.inf]          # the cut at 2 is gone
    assert counts == [10, 50] and bads == [1, 5]


def test_coarse_edges_makes_bad_rate_monotonic():
    # 4 bins of 25 people; bad rates 40%, 20%, 28%, 8% -> bin 2 goes the wrong way
    x = pd.Series([1.0] * 25 + [2.0] * 25 + [3.0] * 25 + [4.0] * 25)
    y = pd.Series([1] * 10 + [0] * 15 + [1] * 5 + [0] * 20 + [1] * 7 + [0] * 18 + [1] * 2 + [0] * 23)
    edges = coarse_edges(x, y, [-np.inf, 1, 2, 3, np.inf], min_share=0.05)
    assert edges == [-np.inf, 1, 3, np.inf]       # bins 2 and 3 were joined: 40% -> 24% -> 8%


def test_coarse_edges_merges_tiny_bins():
    x = pd.Series([0.0] * 97 + [5.0] * 3)          # value 5 is only 3% of customers
    y = pd.Series([0] * 90 + [1] * 7 + [1] * 3)
    assert coarse_edges(x, y, [-np.inf, 0, np.inf], min_share=0.05) == [-np.inf, np.inf]


def test_select_features_drops_a_copy_and_weak_ones():
    a = pd.Series(np.arange(100.0))
    woe = pd.DataFrame({"strong": a, "copy_of_strong": a * 2 + 1, "other": np.sin(a), "weak": a % 3})
    specs = {"strong": {"iv": 0.4}, "copy_of_strong": {"iv": 0.3}, "other": {"iv": 0.1}, "weak": {"iv": 0.01}}
    kept, dropped = select_features(woe, specs, min_iv=0.02, max_corr=0.6, max_features=15)
    assert kept == ["strong", "other"]
    assert dropped["copy_of_strong"].startswith("repeats strong")
    assert dropped["weak"] == "IV below minimum"