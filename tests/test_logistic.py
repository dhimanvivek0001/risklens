"""Tests for Phase 3 lesson 9c: hand-written logistic regression.
Run:  python -m pytest -q
"""

import numpy as np
import pandas as pd

from risklens.models.logistic import fit_logistic, predict_proba, sigmoid
from risklens.models.train_scorecard import clean_fit


def test_sigmoid():
    assert sigmoid(0) == 0.5                                   # 50/50 in the middle
    assert sigmoid(10) > 0.99 and sigmoid(-10) < 0.01


def test_fit_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20_000, 2))
    true = np.array([-2.0, 1.0, -0.5])                         # intercept, b1, b2
    y = (rng.random(20_000) < sigmoid(true[0] + X @ true[1:])).astype(int)
    beta, se, pvalues = fit_logistic(X, y)
    assert np.allclose(beta, true, atol=0.1)                   # it finds the numbers we hid
    assert (pvalues[1:] < 0.001).all()                         # both features clearly matter
    p = predict_proba(X, beta)
    assert abs(p.mean() - y.mean()) < 0.001                    # predictions add up to the real bad rate


def test_clean_fit_removes_noise_feature():
    rng = np.random.default_rng(1)
    X = pd.DataFrame({"useful": rng.normal(size=5000), "noise": rng.normal(size=5000)})
    y = (rng.random(5000) < sigmoid(-2 - 1.0 * X["useful"])).astype(int)
    coefs, removed = clean_fit(X, y, ["useful", "noise"])
    assert coefs["feature"].tolist() == ["intercept", "useful"]
    assert removed[0][0] == "noise"