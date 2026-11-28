"""Phase 3 step 1: split the data and rank every feature by Information Value.

1. Split the 307,511 training applications into train / valid / test (60/20/20)
   and save the split in DuckDB so every later step uses the same customers.
2. Fit WoE bins on the TRAIN part only.
3. Write reports/03_iv_ranking.md.

Run:
  python -m risklens.models.iv_report
"""

import duckdb
import numpy as np
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.features.build import FINAL_TABLE, ID_COLS
from risklens.models.woe import fit_feature, iv_strength

SPLIT_TABLE = "features.model_split"
NEVER_MODEL = {"CODE_GENDER"}   # kept only for the fairness check in Phase 7


def make_split(target, seed=42, shares=(0.6, 0.2, 0.2)):
    """Random 60/20/20 split, done separately for goods and bads (stratified)."""
    rng = np.random.default_rng(seed)
    split = pd.Series("", index=target.index, dtype=object)
    for value in (0, 1):
        rows = rng.permutation(target.index[target == value].to_numpy())
        n_train = round(len(rows) * shares[0])
        n_valid = round(len(rows) * shares[1])
        split[rows[:n_train]] = "train"
        split[rows[n_train:n_train + n_valid]] = "valid"
        split[rows[n_train + n_valid:]] = "test"
    return split


def save_split(con, df):
    """Store (SK_ID_CURR, split) in the warehouse."""
    con.register("split_df", df[["SK_ID_CURR", "split"]])
    con.execute(f"CREATE OR REPLACE TABLE {SPLIT_TABLE} AS SELECT * FROM split_df").fetchall()
    con.unregister("split_df")


def check_split(df):
    """Fail fast if the split is wrong."""
    summary = df.groupby("split")["TARGET"].agg(rows="size", bad_rate="mean")
    assert set(summary.index) == {"train", "valid", "test"}, "missing a split"
    assert summary["rows"].sum() == len(df), "some applications were not assigned"
    spread = summary["bad_rate"].max() - summary["bad_rate"].min()
    assert spread < 0.002, f"bad rates differ too much between splits: {spread:.4f}"
    return summary


def rank_features(train, cfg):
    """Fit WoE bins for every feature on train data and return them sorted by IV."""
    features = [c for c in train.columns if c not in ID_COLS | NEVER_MODEL | {"split"}]
    specs = {c: fit_feature(train[c], train["TARGET"], cfg["max_bins"], cfg["min_bin_share"])
             for c in features}
    return dict(sorted(specs.items(), key=lambda kv: kv[1]["iv"], reverse=True))


def build_report(summary, specs, example):
    lines = [
        "# 03 - Information Value ranking",
        "",
        "## Train / valid / test split",
        "",
        "| Split | Applications | Bad rate |",
        "| --- | --- | --- |",
    ]
    for name in ("train", "valid", "test"):
        lines.append(f"| {name} | {int(summary.loc[name, 'rows']):,} | {summary.loc[name, 'bad_rate']:.2%} |")

    counts = pd.Series([iv_strength(s["iv"]) for s in specs.values()]).value_counts()
    lines += ["", "## How many features in each IV band", "", "| Strength | Features |", "| --- | --- |"]
    for band in ("suspicious - check for leakage", "strong", "medium", "weak", "useless"):
        lines.append(f"| {band} | {int(counts.get(band, 0))} |")

    lines += [
        "",
        "## All features by IV (fitted on train only)",
        "",
        "| Rank | Feature | IV | Strength | Bins |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rank, (name, s) in enumerate(specs.items(), start=1):
        lines.append(f"| {rank} | {name} | {s['iv']:.3f} | {iv_strength(s['iv'])} | {len(s['table'])} |")

    t = specs[example]["table"]
    lines += [
        "",
        f"## Example WoE table: {example}",
        "",
        "| Bin | Customers | Bad rate | WoE | IV part |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, r in t.iterrows():
        lines.append(f"| {r['bin']} | {int(r['count']):,} | {r['bad_rate']:.2%} | {r['woe']:+.3f} | {r['iv']:.4f} |")
    lines.append("")
    return "\n".join(lines)


def run(db_file=None, reports_dir=None, example="EXT_SOURCE_2"):
    settings = load_settings()
    cfg = settings["scorecard"]
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = reports_dir or PROJECT_ROOT / settings["paths"]["reports_dir"]

    with duckdb.connect(str(db_file)) as con:
        df = con.execute(f"SELECT * FROM {FINAL_TABLE} WHERE is_train = 1").df()
        df["TARGET"] = df["TARGET"].astype(int)
        df["split"] = make_split(df["TARGET"], cfg["random_seed"], tuple(cfg["split"]))
        summary = check_split(df)
        save_split(con, df)

    train = df[df["split"] == "train"]
    specs = rank_features(train, cfg)
    report = build_report(summary, specs, example)
    out = reports_dir / "03_iv_ranking.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {out}")
    return specs


if __name__ == "__main__":
    run()