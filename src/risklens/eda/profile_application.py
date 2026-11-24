"""Phase 1 profiling of raw.application_train + baseline policy profit.

Writes reports/01_eda_application.md — the first evidence for the problem-framing doc.

Run (after risklens.data.load):
  python -m risklens.eda.profile_application
"""

from pathlib import Path

import duckdb
import pandas as pd

from risklens import PROJECT_ROOT, load_settings
from risklens.economics.profit_matrix import Economics, policy_profit

KEY_COLUMNS = [
    "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "DAYS_BIRTH",
    "DAYS_EMPLOYED", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
]


def load_application(db_file: Path) -> pd.DataFrame:
    with duckdb.connect(str(db_file), read_only=True) as con:
        return con.execute("SELECT * FROM raw.application_train").df()


def baseline_approve(df: pd.DataFrame, rules: dict) -> pd.Series:
    """Rule-based policy a small lender might use today."""
    credit_income = df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]
    decline = (df["EXT_SOURCE_2"].fillna(0) < rules["ext_source_2_min"]) | (
        credit_income > rules["credit_income_ratio_max"]
    )
    return ~decline


def bad_rate_by_band(df: pd.DataFrame, col: str, bins: int = 5) -> pd.DataFrame:
    banded = pd.qcut(df[col], q=bins, duplicates="drop")
    out = df.groupby(banded, observed=True)["TARGET"].agg(applications="size", bad_rate="mean")
    out.index = [f"{iv.left:.2f} – {iv.right:.2f}" for iv in out.index]
    out["applications"] = out["applications"].astype(int)
    return out


def build_report(df: pd.DataFrame, settings: dict) -> str:
    econ = Economics(**{k: settings["economics"][k] for k in ("net_margin", "lgd")})
    lines: list[str] = ["# 01 — EDA: application_train", ""]

    # Size and target
    bad_rate = df["TARGET"].mean()
    lines += [
        "## Size and target",
        "",
        f"- Applications: **{len(df):,}**",
        f"- Columns: **{df.shape[1]}**",
        f"- Bad rate (TARGET=1): **{bad_rate:.2%}**",
        f"- Break-even bad rate (margin {econ.net_margin:.0%}, LGD {econ.lgd:.0%}): "
        f"**{econ.break_even_bad_rate:.2%}**",
        "",
    ]

    # Missing values
    missing = df.isna().mean().sort_values(ascending=False)
    top_missing = missing[missing > 0].head(15)
    lines += ["## Top 15 columns by missing share", "", "| Column | Missing |", "| --- | --- |"]
    lines += [f"| {c} | {v:.1%} |" for c, v in top_missing.items()]
    lines += ["", f"Columns with >50% missing: **{int((missing > 0.5).sum())}**", ""]

    # Known data quirk
    if "DAYS_EMPLOYED" in df:
        anomaly = (df["DAYS_EMPLOYED"] == 365243).mean()
        lines += [
            "## Data quality flags",
            "",
            f"- `DAYS_EMPLOYED = 365243` (placeholder, not a real value): **{anomaly:.1%}** of rows "
            "— treat as missing and add a flag feature.",
            "",
        ]

    # Key numeric summary
    present = [c for c in KEY_COLUMNS if c in df]
    desc = df[present].describe().T[["mean", "50%", "min", "max"]]
    lines += ["## Key numeric columns", "", "| Column | Mean | Median | Min | Max |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {c} | {r['mean']:,.3f} | {r['50%']:,.3f} | {r['min']:,.3f} | {r['max']:,.3f} |" for c, r in desc.iterrows()]
    lines.append("")

    # Risk by external score — the strongest single signal in this dataset
    if "EXT_SOURCE_2" in df:
        bands = bad_rate_by_band(df.dropna(subset=["EXT_SOURCE_2"]), "EXT_SOURCE_2")
        lines += ["## Bad rate by EXT_SOURCE_2 quintile", "", "| Band | Applications | Bad rate |", "| --- | --- | --- |"]
        lines += [f"| {i} | {int(r['applications']):,} | {r['bad_rate']:.2%} |" for i, r in bands.iterrows()]
        lines.append("")

    # Baseline policy economics
    approve = baseline_approve(df, settings["baseline_rules"])
    base = policy_profit(approve, df["TARGET"], df["AMT_CREDIT"], econ)
    approve_all = policy_profit(pd.Series(True, index=df.index), df["TARGET"], df["AMT_CREDIT"], econ)
    lines += [
        "## Baseline policy economics",
        "",
        "| Policy | Approval rate | Bad rate (approved) | Bads declined | Profit per 10k apps* |",
        "| --- | --- | --- | --- | --- |",
        f"| Approve everyone | {approve_all['approval_rate']:.1%} | {approve_all['bad_rate_approved']:.2%} | "
        f"{approve_all['bads_declined_share']:.1%} | {approve_all['profit_per_10k_apps']:,.0f} |",
        f"| Rule-based baseline | {base['approval_rate']:.1%} | {base['bad_rate_approved']:.2%} | "
        f"{base['bads_declined_share']:.1%} | {base['profit_per_10k_apps']:,.0f} |",
        "",
        "*In the dataset's own currency units (Home Credit does not state the currency). "
        "Compare policies with each other, not as real euros.",
        "",
        f"Business constraint: approval rate ≥ {settings['economics']['min_approval_rate']:.0%}. "
        "This is the number every model in later phases has to beat.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    settings = load_settings()
    db_file = PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = PROJECT_ROOT / settings["paths"]["reports_dir"]
    reports_dir.mkdir(parents=True, exist_ok=True)

    df = load_application(db_file)
    report = build_report(df, settings)
    out = reports_dir / "01_eda_application.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
