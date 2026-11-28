"""Phase 4 lesson 10a: calibration check + the most profitable approval cut-off.

1. Calibration: when the model says "5% chance of default", do about 5% really default?
2. Cut-off: approve everyone with score >= cut-off. Try every cut-off on VALID,
   keep the one with the highest profit that still approves at least 70% of applicants.
3. Final check on TEST: compare our policy with approve-everyone and the Phase 1 rules.

Run:
  python -m risklens.decisions.cutoff
"""

import duckdb
import numpy as np
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.economics.profit_matrix import Economics, policy_profit
from risklens.eda.profile_application import baseline_approve
from risklens.features.build import FINAL_TABLE
from risklens.models.final_scorecard import SCORES_TABLE


def calibration_table(pd_pred, y, n_groups=10):
    """Group customers by predicted PD and compare predicted vs actual bad rate."""
    t = pd.DataFrame({"pd": np.asarray(pd_pred), "bad": np.asarray(y)})
    t["group"] = pd.qcut(t["pd"], n_groups, labels=False, duplicates="drop")
    table = t.groupby("group").agg(customers=("bad", "size"), predicted=("pd", "mean"), actual=("bad", "mean"))
    error = float((table["customers"] * (table["predicted"] - table["actual"]).abs()).sum() / len(t))
    return table.reset_index(drop=True), error


def cutoff_curve(score, target, amount, econ, cutoffs):
    """Profit and approval rate for every possible cut-off."""
    rows = []
    for c in cutoffs:
        result = policy_profit(score >= c, target, amount, econ)
        rows.append({"cutoff": c, **result})
    return pd.DataFrame(rows)


def choose_cutoff(curve, min_approval_rate):
    """Highest-profit cut-off among those that approve enough applicants."""
    allowed = curve[curve["approval_rate"] >= min_approval_rate]
    return allowed.loc[allowed["total_profit"].idxmax()]


def load_decision_data(con):
    return con.execute(f"""
        SELECT s.*, f.AMT_CREDIT, f.AMT_INCOME_TOTAL, f.EXT_SOURCE_2
        FROM {SCORES_TABLE} s
        JOIN {FINAL_TABLE} f USING (SK_ID_CURR)
    """).df()


def build_report(econ, min_rate, calib, curve, best, best_free, policies):
    lines = [
        "# 07 - Decision policy: calibration and profit cut-off",
        "",
        f"Economics: margin **{econ.net_margin:.0%}** on good loans, loss **{econ.lgd:.0%}** on bad loans. "
        f"Break-even bad rate = **{econ.break_even_bad_rate:.2%}**. Profit in dataset currency units.",
        "",
        "## 1. Calibration (does predicted PD match reality?)",
        "",
    ]
    for name, (table, error) in calib.items():
        lines += [f"### {name}", "", "| PD group | Customers | Predicted PD | Actual bad rate |",
                  "| --- | --- | --- | --- |"]
        for i, r in table.iterrows():
            lines.append(f"| {i + 1} | {int(r['customers']):,} | {r['predicted']:.2%} | {r['actual']:.2%} |")
        lines += ["", f"Average calibration error: **{error:.2%}**", ""]

    lines += ["## 2. Profit by cut-off (valid set)", "",
              "| Cut-off | Approval rate | Bad rate of approved | Profit per 10k applications |",
              "| --- | --- | --- | --- |"]
    shown = curve[(curve["cutoff"] % 10 == 0) | (curve["cutoff"] == best["cutoff"])]
    for _, r in shown.iterrows():
        mark = " **<- chosen**" if r["cutoff"] == best["cutoff"] else ""
        lines.append(f"| {int(r['cutoff'])}{mark} | {r['approval_rate']:.1%} | {r['bad_rate_approved']:.2%} "
                     f"| {r['profit_per_10k_apps']:,.0f} |")
    lines += ["",
              f"- Best cut-off with no approval limit: **{int(best_free['cutoff'])}** "
              f"(approves {best_free['approval_rate']:.1%})",
              f"- Best cut-off approving at least {min_rate:.0%}: **{int(best['cutoff'])}** "
              f"(approves {best['approval_rate']:.1%})", ""]

    lines += ["## 3. Final comparison on the test set", "",
              "| Policy | Approval rate | Bad rate of approved | Bads caught | Profit per 10k applications |",
              "| --- | --- | --- | --- | --- |"]
    for name, r in policies.items():
        lines.append(f"| {name} | {r['approval_rate']:.1%} | {r['bad_rate_approved']:.2%} "
                     f"| {r['bads_declined_share']:.1%} | {r['profit_per_10k_apps']:,.0f} |")
    base = policies["Approve everyone"]["profit_per_10k_apps"]
    ours = policies[f"Scorecard, cut-off {int(best['cutoff'])}"]["profit_per_10k_apps"]
    rules = policies["Phase 1 rules"]["profit_per_10k_apps"]
    lines += ["", f"Scorecard vs approve everyone: **{ours - base:+,.0f}** per 10k applications.",
              f"Scorecard vs Phase 1 rules: **{ours - rules:+,.0f}** per 10k applications.", ""]
    return "\n".join(lines)


def run(db_file=None, reports_dir=None):
    settings = load_settings()
    econ = Economics(settings["economics"]["net_margin"], settings["economics"]["lgd"])
    min_rate = settings["economics"]["min_approval_rate"]
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = reports_dir or PROJECT_ROOT / settings["paths"]["reports_dir"]

    with duckdb.connect(str(db_file), read_only=True) as con:
        df = load_decision_data(con)
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]

    calib = {name: calibration_table(part["pd"], part["TARGET"]) for name, part in (("valid", valid), ("test", test))}

    cutoffs = range(int(valid["score"].min()), int(valid["score"].max()) + 1)
    curve = cutoff_curve(valid["score"], valid["TARGET"], valid["AMT_CREDIT"], econ, cutoffs)
    best = choose_cutoff(curve, min_rate)
    best_free = choose_cutoff(curve, 0.0)

    c = int(best["cutoff"])