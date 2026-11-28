"""Logistic regression written by hand (Newton-Raphson), with p-values.

The model:   P(bad) = 1 / (1 + e^-(b0 + b1*x1 + b2*x2 + ...))
fit() finds the b's that make the observed goods and bads most likely.
"""

import math

import numpy as np


def sigmoid(z):
    """Squash any number into a probability between 0 and 1."""
    return 1 / (1 + np.exp(-z))


def fit_logistic(X, y, max_iter=25, tol=1e-8):
    """Return coefficients (intercept first), standard errors and p-values."""
    X1 = np.column_stack([np.ones(len(X)), X])          # column of 1s = the intercept b0
    y = np.asarray(y, dtype="float64")
    beta = np.zeros(X1.shape[1])                         # start with every b = 0
    for _ in range(max_iter):
        p = sigmoid(X1 @ beta)                           # current guess of P(bad) per customer
        gradient = X1.T @ (y - p)                        # which way each b should move
        hessian = X1.T @ (X1 * (p * (1 - p))[:, None])   # how curved the hill is
        step = np.linalg.solve(hessian, gradient)        # Newton step towards the top
        beta = beta + step
        if np.max(np.abs(step)) < tol:                   # steps are tiny = we have arrived
            break
    p = sigmoid(X1 @ beta)
    hessian = X1.T @ (X1 * (p * (1 - p))[:, None])
    se = np.sqrt(np.diag(np.linalg.inv(hessian)))        # uncertainty of each b
    z = beta / se
    pvalues = np.array([math.erfc(abs(v) / math.sqrt(2)) for v in z])   # two-sided normal test
    return beta, se, pvalues


def predict_proba(X, beta):
    """P(bad) for new customers, using the fitted coefficients."""
    X1 = np.column_stack([np.ones(len(X)), X])
    return sigmoid(X1 @ beta)