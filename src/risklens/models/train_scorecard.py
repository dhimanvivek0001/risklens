"""Phase 3 lesson 9c: train the logistic regression on the WoE features.

1. Rebuild the 9b bins and feature list (train data only)
2. Fit logistic regression on train
3. Clean the model: drop any feature with the wrong sign or a weak p-value, refit
4. Measure Gini on train and valid (test stays locked until the end)

Run:
  python -m risklens.models.train_scorecard
"""

import duckdb
import numpy as np
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.features.build import univariate_gini
from risklens.models.iv_report import rank_features
from risklens.models.logistic import fit_logistic, predict_proba
from risklens.models.scorecard import coarse_class, load_model_data, select_features
from risklens.models.woe import transform


def woe_frame(df, specs, features):
    """Every customer's WoE value for each feature."""
    return pd.DataFrame({c: transform(df[c], specs[c]) for c in features})


def clean_fit(X, y, features, max_pvalue=0.05):
    """Fit, then remove the worst offending feature and refit, until every coefficient is sensible.

    WoE is ln(good/bad): higher WoE = safer. We predict BAD, so every coefficient must be NEGATIVE.
    """
    features = list(features)
    removed = []
    while True:
        beta, se, pvalues = fit_logistic(X[features].to_numpy(), y)
        coefs = pd.DataFrame({"feature": ["intercept", *features], "coef": beta, "se": se, "p_value": pvalues})
        body = coefs.iloc[1:]
        wrong_sign = body[body["coef"] >= 0]
        weak = body[body["p_value"] > max_pvalue]
        if wrong_sign.empty and weak.empty:
            return coefs, removed
        if not wrong_sign.empty:
            worst = wrong_sign.sort_values("coef", ascending=False).iloc[0]
            reason = f"wrong sign (coef {worst['coef']:+.3f})"
        else:
            worst = weak.sort_values("p_value", ascending=False).iloc[0]
            reason = f"not significant (p = {worst['p_value']:.3f})"
        features.remove(worst["feature"])
        removed.append((worst["feature"], reason))


def build_report(coefs, removed, ginis):
    lines = [
        "# 05 - Logistic regression scorecard model",
        "",
        "## How well it ranks customers (Gini)",
        "",
        "| Data | Customers | Gini |",
        "| --- | --- | --- |",
    ]
    for name, (n, g) in ginis.items():
        lines.append(f"| {name} | {n:,} | {g:.3f} |")
    gap = ginis["train"][1] - ginis["valid"][1]
    lines += ["", f"Train - valid gap: **{gap:+.3f}** "
              f"({'OK, no sign of overfitting' if abs(gap) < 0.03 else 'CHECK: model may be overfitting'})", ""]

    lines += ["## Coefficients", "",
              "Every feature coefficient must be negative (higher WoE = safer = lower chance of default).", "",
              "| Feature | Coefficient | Std error | p-value |", "| --- | --- | --- | --- |"]
    for _, r in coefs.iterrows():
        lines.append(f"| {r['feature']} | {r['coef']:+.4f} | {r['se']:.4f} | {r['p_value']:.2g} |")

    lines += ["", "## Removed during cleaning", ""]
    if removed:
        lines += ["| Feature | Reason |", "| --- | --- |"]
        lines += [f"| {f} | {why} |" for f, why in removed]
    else:
        lines.append("None - every selected feature passed.")
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
    valid = df[df["split"] == "valid"]

    # 9a + 9b again: bins and features are learnt from train only
    coarse = coarse_class(train, rank_features(train, cfg), cfg["min_bin_share"])
    all_woe = woe_frame(train, coarse, coarse)
    kept, _ = select_features(all_woe, coarse, cfg["min_iv"], cfg["max_corr"], cfg["max_features"])

    # 9c: fit and clean
    X_train = woe_frame(train, coarse, kept)
    coefs, removed = clean_fit(X_train, train["TARGET"], kept, cfg["max_pvalue"])
    final = coefs["feature"].iloc[1:].tolist()
    beta = coefs["coef"].to_numpy()

    ginis = {}
    for name, part in (("train", train), ("valid", valid)):
        p = predict_proba(woe_frame(part, coarse, final).to_numpy(), beta)
        ginis[name] = (len(part), univariate_gini(pd.Series(p), part["TARGET"].reset_index(drop=True)))

    report = build_report(coefs, removed, ginis)
    out = reports_dir / "05_logistic_model.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {out}")
    return coarse, coefs


if __name__ == "__main__":
    run()