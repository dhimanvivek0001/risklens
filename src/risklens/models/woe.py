"""Weight of Evidence (WoE) binning, written by hand.

For each feature we cut the customers into bins (groups) and ask:
"are there more goods or more bads in this bin than on average?"

  WoE of a bin = ln( share of all goods in the bin / share of all bads in the bin )
      WoE > 0  -> safer than average      WoE < 0  -> riskier than average

  IV (Information Value) = sum over bins of (share_good - share_bad) x WoE
      one number per feature: how well it separates good from bad customers
"""

import numpy as np
import pandas as pd

MISSING = "Missing"
OTHER = "Other"
SMOOTHING = 0.5   # added to every count so an empty bin never gives ln(0)


def numeric_edges(x, max_bins=10):
    """Cut points that put roughly the same number of customers in each bin."""
    values = x.dropna()
    if values.nunique() < 2:
        return [-np.inf, np.inf]
    inner = np.quantile(values, np.linspace(0, 1, max_bins + 1)[1:-1])
    inner = np.unique(inner[inner < values.max()])
    return [-np.inf, *inner.tolist(), np.inf]


def assign_bins(x, spec):
    """Turn raw values into bin labels, e.g. '03: (0.31, 0.45]' or 'Missing'."""
    out = pd.Series(MISSING, index=x.index, dtype=object)
    if spec["type"] == "numeric":
        edges = spec["edges"]
        labels = np.array(
            [f"{i:02d}: ({edges[i]:.4g}, {edges[i + 1]:.4g}]" for i in range(len(edges) - 1)],
            dtype=object,
        )
        codes = pd.cut(x.astype("float64"), bins=edges, labels=False, right=True)
        known = codes.notna()
        out[known] = labels[codes[known].astype(int)]
    else:
        known = x.notna()
        out[known] = np.where(x[known].isin(spec["keep"]), x[known].astype(str), OTHER)
    return out


def woe_table(bins, y):
    """Count goods and bads in every bin and work out WoE and IV."""
    df = pd.DataFrame({"bin": bins.to_numpy(), "bad": y.to_numpy()})
    t = df.groupby("bin").agg(count=("bad", "size"), bads=("bad", "sum"))
    t["goods"] = t["count"] - t["bads"]
    k = len(t)
    t["share_good"] = (t["goods"] + SMOOTHING) / (t["goods"].sum() + SMOOTHING * k)
    t["share_bad"] = (t["bads"] + SMOOTHING) / (t["bads"].sum() + SMOOTHING * k)
    t["bad_rate"] = t["bads"] / t["count"]
    t["woe"] = np.log(t["share_good"] / t["share_bad"])
    t["iv"] = (t["share_good"] - t["share_bad"]) * t["woe"]
    return t.reset_index()


def fit_feature(x, y, max_bins=10, min_share=0.05):
    """Learn the bins and their WoE from TRAINING data only."""
    if pd.api.types.is_numeric_dtype(x):
        x = x.astype("float64")
        spec = {"type": "numeric", "edges": numeric_edges(x, max_bins)}
    else:
        shares = x.value_counts(normalize=True)
        spec = {"type": "categorical", "keep": sorted(shares[shares >= min_share].index)}
    table = woe_table(assign_bins(x, spec), y)
    spec["table"] = table
    spec["woe"] = dict(zip(table["bin"], table["woe"]))
    spec["iv"] = float(table["iv"].sum())
    return spec


def transform(x, spec):
    """Replace each value by the WoE of its bin. A bin never seen in training gets 0 (= average)."""
    return assign_bins(x, spec).map(spec["woe"]).astype("float64").fillna(0.0)


def iv_strength(iv):
    """The rule of thumb credit teams use to read IV."""
    if iv < 0.02:
        return "useless"
    if iv < 0.10:
        return "weak"
    if iv < 0.30:
        return "medium"
    if iv < 0.50:
        return "strong"
    return "suspicious - check for leakage"