"""Phase 3: build the credit scorecard.

Lesson 9b - coarse classing + feature selection
  Fine classing (9a) gave up to 10 bins per feature. A scorecard needs fewer, cleaner bins:
    1. every bin holds at least 5% of customers (tiny bins are noisy)
    2. the bad rate moves in ONE direction across the bins (monotonic) - easy to explain
  Then we keep a small set of strong features that do not repeat each other.

Run:
  python -m risklens.models.scorecard
"""

import duckdb
import numpy as np
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.features.build import FINAL_TABLE
from risklens.models.iv_report import SPLIT_TABLE, rank_features
from risklens.models.woe import MISSING, assign_bins, iv_strength, transform, woe_table


def merge_bins(edges, counts, bads, i):
    """Join bin i and bin i+1 into one bin by removing the cut point between them."""
    edges = edges[:i + 1] + edges[i + 2:]
    counts = counts[:i] + [counts[i] + counts[i + 1]] + counts[i + 2:]
    bads = bads[:i] + [bads[i] + bads[i + 1]] + bads[i + 2:]
    return edges, counts, bads


def coarse_edges(x, y, edges, min_share=0.05):
    """Merge neighbouring bins until every bin is big enough and the bad rate is monotonic."""
    x = x.astype("float64")
    known = x.notna()
    codes = pd.cut(x[known], bins=edges, labels=False, right=True).astype(int).to_numpy()
    k = len(edges) - 1
    counts = np.bincount(codes, minlength=k).tolist()
    bads = np.bincount(codes, weights=y[known].to_numpy(), minlength=k).tolist()
    edges = list(edges)

    # Rule 1: no bin smaller than min_share of all customers
    while len(counts) > 1 and min(counts) < min_share * len(x):
        i = counts.index(min(counts))
        rate = bads[i] / counts[i] if counts[i] else 0
        if i == len(counts) - 1:
            i -= 1                                    # last bin can only join the one before it
        elif i > 0:
            left = abs(bads[i - 1] / counts[i - 1] - rate)
            right = abs(bads[i + 1] / counts[i + 1] - rate)
            if left < right:
                i -= 1                                # join the neighbour with the closer bad rate
        edges, counts, bads = merge_bins(edges, counts, bads, i)

    # Rule 2: bad rate must only go up, or only go down
    while len(counts) > 1:
        r = [b / c for b, c in zip(bads, counts)]
        going_up = r[-1] >= r[0]
        wrong_way = [i for i in range(len(r) - 1)
                     if (going_up and r[i + 1] < r[i]) or (not going_up and r[i + 1] > r[i])]
        if not wrong_way:
            break
        edges, counts, bads = merge_bins(edges, counts, bads, wrong_way[0])
    return edges


def fit_with_edges(x, y, edges):
    """Same as fit_feature, but with cut points we chose ourselves."""
    spec = {"type": "numeric", "edges": edges}
    table = woe_table(assign_bins(x.astype("float64"), spec), y)
    spec["table"] = table
    spec["woe"] = dict(zip(table["bin"], table["woe"]))
    spec["iv"] = float(table["iv"].sum())
    return spec


def coarse_class(train, fine_specs, min_share):
    """Coarse-class every numeric feature. Text features keep their bins from 9a."""
    coarse = {}
    for name, spec in fine_specs.items():
        if spec["type"] == "numeric":
            edges = coarse_edges(train[name], train["TARGET"], spec["edges"], min_share)
            coarse[name] = fit_with_edges(train[name], train["TARGET"], edges)
        else:
            coarse[name] = spec
    return coarse


def select_features(train_woe, specs, min_iv=0.02, max_corr=0.6, max_features=15):
    """Walk down the IV ranking and keep a feature only if it adds something new."""
    corr = train_woe.corr().abs()
    kept, dropped = [], {}
    for name in sorted(specs, key=lambda c: specs[c]["iv"], reverse=True):
        if specs[name]["iv"] < min_iv:
            dropped[name] = "IV below minimum"
            continue
        clash = [k for k in kept if corr.loc[name, k] > max_corr]
        if clash:
            dropped[name] = f"repeats {clash[0]} (correlation {corr.loc[name, clash[0]]:.2f})"
            continue
        if len(kept) >= max_features:
            dropped[name] = "already have enough features"
            continue
        kept.append(name)
    return kept, dropped


def load_model_data(con):
    """Features + split label for the 307,511 customers with a known outcome."""
    df = con.execute(
        f"SELECT f.*, s.split FROM {FINAL_TABLE} f JOIN {SPLIT_TABLE} s USING (SK_ID_CURR)"
    ).df()
    df["TARGET"] = df["TARGET"].astype(int)
    return df


def build_report(fine, coarse, kept, dropped):
    lines = [
        "# 04 - Scorecard features (coarse classing + selection)",
        "",
        f"Selected **{len(kept)}** features out of {len(coarse)}.",
        "",
        "## Selected features",
        "",
        "| # | Feature | Bins 9a -> now | IV 9a -> now | Strength |",
        "| --- | --- | --- | --- | --- |",
    ]
    for n, name in enumerate(kept, start=1):
        lines.append(
            f"| {n} | {name} | {len(fine[name]['table'])} -> {len(coarse[name]['table'])} "
            f"| {fine[name]['iv']:.3f} -> {coarse[name]['iv']:.3f} | {iv_strength(coarse[name]['iv'])} |"
        )

    lines += ["", "## Dropped because they repeat a stronger feature", "", "| Feature | IV | Reason |",
              "| --- | --- | --- |"]
    for name, why in dropped.items():
        if why.startswith("repeats"):
            lines.append(f"| {name} | {coarse[name]['iv']:.3f} | {why} |")
    low = sum(why == "IV below minimum" for why in dropped.values())
    enough = sum(why == "already have enough features" for why in dropped.values())
    lines += ["", f"Also dropped: **{low}** with IV below the minimum, "
              f"**{enough}** because the feature limit was reached.", ""]

    lines += ["## Bins of every selected feature", ""]
    for name in kept:
        lines += [f"### {name}", "", "| Bin | Customers | Bad rate | WoE |", "| --- | --- | --- | --- |"]
        for _, r in coarse[name]["table"].iterrows():
            lines.append(f"| {r['bin']} | {int(r['count']):,} | {r['bad_rate']:.2%} | {r['woe']:+.3f} |")
        lines.append("")
    return "\n".join(lines)


def run(db_file=None, reports_dir=None):
    settings = load_settings()
    cfg = settings["scorecard"]
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = reports_dir or PROJECT_ROOT / settings["paths"]["reports_dir"]

    with duckdb.connect(str(db_file), read_only=True) as con:
        df = load_model_data(con)
    train = df[df["split"] == "train"]

    fine = rank_features(train, cfg)                                   # 9a: fine bins
    coarse = coarse_class(train, fine, cfg["min_bin_share"])           # 9b: clean bins
    train_woe = pd.DataFrame({c: transform(train[c], coarse[c]) for c in coarse})
    kept, dropped = select_features(train_woe, coarse, cfg["min_iv"], cfg["max_corr"], cfg["max_features"])

    report = build_report(fine, coarse, kept, dropped)
    out = reports_dir / "04_scorecard_features.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {out}")
    return df, coarse, kept


if __name__ == "__main__":
    run()