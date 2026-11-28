"""Turn the logistic regression into a points scorecard.

Industry convention ("points to double the odds"):
  score = offset + factor x ln(odds of being good)
  factor = PDO / ln(2)          -> every PDO points, the odds of being good double
  offset = base_score - factor x ln(base_odds)
With base 600, odds 50:1 and PDO 20: a 600 customer is 50:1 good, 620 is 100:1, 580 is 25:1.
"""

import math

import numpy as np
import pandas as pd

from risklens.models.woe import assign_bins


def scaling(base_score=600, base_odds=50, pdo=20):
    """Return (factor, offset) for the score formula."""
    factor = pdo / math.log(2)
    offset = base_score - factor * math.log(base_odds)
    return factor, offset


def scorecard_table(coefs, specs, factor, offset):
    """Points for every bin of every feature. Higher points = safer."""
    b0 = coefs["coef"].iloc[0]
    features = coefs.iloc[1:]
    n = len(features)
    neutral = round(-(b0 / n) * factor + offset / n)          # points for a bin never seen in train
    rows = []
    for _, f in features.iterrows():
        for bin_label, woe in specs[f["feature"]]["woe"].items():
            points = -(f["coef"] * woe + b0 / n) * factor + offset / n
            rows.append({"feature": f["feature"], "bin": bin_label, "woe": woe, "points": round(points)})
    return pd.DataFrame(rows), neutral


def score_customers(df, table, specs, neutral):
    """Add up each customer's points across all scorecard features."""
    total = pd.Series(0, index=df.index, dtype="int64")
    for feature, part in table.groupby("feature", sort=False):
        lookup = dict(zip(part["bin"], part["points"]))
        total += assign_bins(df[feature], specs[feature]).map(lookup).fillna(neutral).astype("int64")
    return total


def ks_statistic(score, y):
    """Biggest gap between the cumulative share of bads and of goods, walking up the score."""
    t = pd.DataFrame({"score": np.asarray(score), "bad": np.asarray(y)})
    g = t.groupby("score")["bad"].agg(bads="sum", n="size").sort_index()
    g["goods"] = g["n"] - g["bads"]
    cum_bad = g["bads"].cumsum() / g["bads"].sum()
    cum_good = g["goods"].cumsum() / g["goods"].sum()
    return float((cum_bad - cum_good).abs().max())


def score_bands(score, y, n_bands=10):
    """Split customers into 10 equal groups by score and show the bad rate of each."""
    t = pd.DataFrame({"score": np.asarray(score), "bad": np.asarray(y)})
    t["band"] = pd.qcut(t["score"], n_bands, labels=False, duplicates="drop")
    return t.groupby("band").agg(
        min_score=("score", "min"), max_score=("score", "max"),
        customers=("bad", "size"), bad_rate=("bad", "mean"),
    ).reset_index(drop=True)