"""Phase 3 lesson 9d: points scorecard + the final exam on the TEST set.

1. Train the model (lesson 9c)
2. Turn coefficients into points (base 600 = odds 50:1, +20 points = odds double)
3. Score every customer and save the scores in DuckDB for Phase 4
4. Open the test set ONCE: Gini, KS and bad rate by score band

Run:
  python -m risklens.models.final_scorecard
"""

import duckdb
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.features.build import univariate_gini
from risklens.models import train_scorecard
from risklens.models.logistic import predict_proba
from risklens.models.points import ks_statistic, scaling, score_bands, score_customers, scorecard_table
from risklens.models.scorecard import load_model_data

SCORES_TABLE = "features.scorecard_scores"


def build_report(cfg, table, neutral, metrics, bands):
    lines = [
        "# 06 - Final credit scorecard",
        "",
        f"Scaling: **{cfg['base_score']} points = odds {cfg['base_odds']}:1 (good:bad)**, "
        f"every **+{cfg['pdo']} points doubles the odds**. Higher score = safer.",
        "",
        "## Results (Gini and KS by data split)",
        "",
        "| Data | Customers | Gini | KS |",
        "| --- | --- | --- | --- |",
    ]
    for name in ("train", "valid", "test"):
        n, gini, ks = metrics[name]
        lines.append(f"| {name} | {n:,} | {gini:.3f} | {ks:.3f} |")

    lines += ["", "## Test set: bad rate by score band (10 equal groups)", "",
              "| Band | Score range | Customers | Bad rate |", "| --- | --- | --- | --- |"]
    for i, r in bands.iterrows():
        lines.append(f"| {i + 1} | {int(r['min_score'])} - {int(r['max_score'])} "
                     f"| {int(r['customers']):,} | {r['bad_rate']:.2%} |")
    ratio = bands["bad_rate"].iloc[0] / bands["bad_rate"].iloc[-1]
    lines += ["", f"Lowest band is **{ratio:.1f}x** as risky as the highest band.", ""]

    lines += ["## The scorecard", "", f"Any value in a bin not seen in training scores **{neutral}** points.", ""]
    for feature, part in table.groupby("feature", sort=False):
        lines += [f"### {feature}", "", "| Bin | Points |", "| --- | --- |"]
        lines += [f"| {r['bin']} | {r['points']} |" for _, r in part.iterrows()]
        lines.append("")
    return "\n".join(lines)


def run(db_file=None, reports_dir=None):
    settings = load_settings()
    cfg = settings["scorecard"]
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = reports_dir or PROJECT_ROOT / settings["paths"]["reports_dir"]

    coarse, coefs = train_scorecard.run(db_file, reports_dir)          # 9c
    with duckdb.connect(str(db_file), read_only=True) as con:
        df = load_model_data(con)

    factor, offset = scaling(cfg["base_score"], cfg["base_odds"], cfg["pdo"])
    table, neutral = scorecard_table(coefs, coarse, factor, offset)
    features = coefs["feature"].iloc[1:].tolist()
    df["score"] = score_customers(df, table, coarse, neutral)
    df["pd"] = predict_proba(train_scorecard.woe_frame(df, coarse, features).to_numpy(), coefs["coef"].to_numpy())

    metrics = {}
    for name in ("train", "valid", "test"):
        part = df[df["split"] == name]
        metrics[name] = (len(part), univariate_gini(part["score"], part["TARGET"]), ks_statistic(part["score"], part["TARGET"]))
    test = df[df["split"] == "test"]
    bands = score_bands(test["score"], test["TARGET"])

    with duckdb.connect(str(db_file)) as con:
        con.register("scores_df", df[["SK_ID_CURR", "split", "TARGET", "score", "pd"]])
        con.execute(f"CREATE OR REPLACE TABLE {SCORES_TABLE} AS SELECT * FROM scores_df").fetchall()
        con.unregister("scores_df")

    report = build_report(cfg, table, neutral, metrics, bands)
    out = reports_dir / "06_scorecard.md"
    out.write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"\nSaved to {out}  |  scores saved to {SCORES_TABLE}")
    return table


if __name__ == "__main__":
    run()