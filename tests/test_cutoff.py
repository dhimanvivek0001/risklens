"""Tests for Phase 4 lesson 10a: calibration and the profit cut-off.
Run:  python -m pytest -q
"""

import numpy as np
import pandas as pd
import pytest

from risklens.decisions.cutoff import calibration_table, choose_cutoff, cutoff_curve
from risklens.economics.profit_matrix import Economics


def test_calibration_perfect_model_has_zero_error():
    pd_pred = np.repeat([0.1, 0.5], 10)                        # 10 people at 10%, 10 at 50%
    y = np.array([1] + [0] * 9 + [1] * 5 + [0] * 5)            # exactly 1 of 10 and 5 of 10 default
    table, error = calibration_table(pd_pred, y, n_groups=2)
    assert table["actual"].tolist() == pytest.approx([0.1, 0.5])
    assert error == pytest.approx(0.0)


def test_cutoff_curve_and_choice():
    econ = Economics(net_margin=0.10, lgd=0.50)
    score = pd.Series([1, 2, 3, 4])
    target = pd.Series([1, 0, 0, 0])                            # the lowest score is the only bad
    amount = pd.Series([1000.0] * 4)
    curve = cutoff_curve(score, target, amount, econ, [1, 2, 3, 4])
    # cut-off 1 approves all: 3 x 100 - 500 = -200 ; cut-off 2 declines the bad: 3 x 100 = +300
    assert curve["total_profit"].tolist() == pytest.approx([-200, 300, 200, 100])
    assert choose_cutoff(curve, 0.0)["cutoff"] == 2
    assert choose_cutoff(curve, 0.9)["cutoff"] == 1           # must approve 90% -> forced to approve all