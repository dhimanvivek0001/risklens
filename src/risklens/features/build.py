"""Phase 2: build one row of features per applicant.

Runs the SQL files in features/sql in order (01 -> 07), checks the result,
and writes reports/02_feature_summary.md.

Run:
  python -m risklens.features.build
"""

import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from risklens import PROJECT_ROOT, load_settings

SQL_DIR = Path(__file__).parent / "sql"
FINAL_TABLE = "features.application_features"
ID_COLS = {"SK_ID_CURR", "TARGET", "is_train"}


def run_sql_files(con, sql_dir=SQL_DIR):
    """Run every .sql file in name order and time each one."""
    for sql_file in sorted(sql_dir.glob("*.sql")):
        start = time.perf_counter()
        con.execute(sql_file.read_text(encoding="utf-8")).fetchall()
        seconds = time.perf_counter() - start
        print(f"{sql_file.name:<32} {seconds:6.1f}s")


def quality_checks(con):
    """Stop the pipeline with a clear message if the feature table is wrong."""
    rows = con.execute(f"SELECT COUNT(*) FROM {FINAL_TABLE}").fetchall()[0][0]
    applications = con.execute("SELECT COUNT(*) FROM staging.application").fetchall()[0][0]
    distinct_ids = con.execute(f"SELECT COUNT(DISTINCT SK_ID_CURR) FROM {FINAL_TABLE}").fetchall()[0][0]
    bad_target = con.execute(
        f"SELECT COUNT(*) FROM {FINAL_TABLE} "
        "WHERE (is_train = 1 AND TARGET IS NULL) OR (is_train = 0 AND TARGET IS NOT NULL)"
    ).fetchall()[0][0]

    assert rows == applications, f"Rows changed in the joins: {rows:,} vs {applications:,}"
    assert distinct_ids == rows, f"Duplicate applicants found: {rows - distinct_ids:,}"
    assert bad_target == 0, f"{bad_target:,} rows have the wrong TARGET for their is_train flag"

    print(f"Quality checks passed: {rows:,} rows, one per applicant, TARGET consistent")
    return {"rows": rows, "distinct_ids": distinct_ids}


def univariate_gini(x, y):
    """How well one feature on its own separates bad (1) from good (0) applicants.

    Gini = |2 * AUC - 1|. 0 = no signal, 1 = perfect separation.
    Missing values are dropped first.
    """
    mask = x.notna()
    x, y = x[mask], y[mask]
    n_bad = int((y == 1).sum())
    n_good = int((y == 0).sum())
    if n_bad == 0 or n_good == 0 or x.nunique() < 2:
        return float("nan")
    ranks = x.rank(method="average")
    auc = (ranks[y == 1].sum() - n_bad * (n_bad + 1) / 2) / (n_bad * n_good)
    return abs(2 * auc - 1)


def build_report(df):
    """Write a markdown summary: coverage of each history, top features, missing values."""
    train = df[df["is_train"] == 1]
    feature_cols = [c for c in df.columns if c not in ID_COLS]
    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]

    lines = [
        "# 02 - Feature summary",
        "",
        f"- Applicants: **{len(df):,}** ({len(train):,} train, {len(df) - len(train):,} test)",
        f"- Features: **{len(feature_cols)}** ({len(numeric_cols)} numeric, "
        f"{len(feature_cols) - len(numeric_cols)} text/categorical)",
        "",
        "## History coverage",
        "",
        "| History | Share of applicants | Bad rate with | Bad rate without |",
        "| --- | --- | --- | --- |",
    ]
    for flag in [c for c in df.columns if c.startswith("has_")]:
        with_h = train.loc[train[flag] == 1, "TARGET"].mean()
        without_h = train.loc[train[flag] == 0, "TARGET"].mean()
        name = flag.removeprefix("has_").replace("_", " ")
        lines.append(f"| {name} | {df[flag].mean():.1%} | {with_h:.2%} | {without_h:.2%} |")

    ginis = {c: univariate_gini(train[c], train["TARGET"]) for c in numeric_cols}
    top = sorted(((g, c) for c, g in ginis.items() if not np.isnan(g)), reverse=True)[:25]
    lines += [
        "",
        "## Top 25 features by stand-alone Gini (train data)",
        "",
        "Gini = |2 x AUC - 1| for each feature on its own. 0 = no signal; "
        "above about 0.10 is useful for a single credit variable.",
        "",
        "| Rank | Feature | Gini | Missing |",
        "| --- | --- | --- | --- |",
    ]
    for rank, (g, c) in enumerate(top, start=1):
        lines.append(f"| {rank} | {c} | {g:.3f} | {df[c].isna().mean():.1%} |")

    missing = df[feature_cols].isna().mean()
    lines += [
        "",
        "## Missing values",
        "",
        f"- Features with no missing values: **{int((missing == 0).sum())}**",
        f"- Features more than 50% missing: **{int((missing > 0.5).sum())}** "
        "(mostly history features: missing = no history, which is itself information)",
        "",
    ]
    return "\n".join(lines)


def build(db_file=None, reports_dir=None):
    """Run the whole Phase 2 pipeline and write the feature report."""
    settings = load_settings()
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    reports_dir = reports_dir or PROJECT_ROOT / settings["paths"]["reports_dir"]
    reports_dir.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(db_file)) as con:
        run_sql_files(con)
        counts = quality_checks(con)
        df = con.execute(f"SELECT * FROM {FINAL_TABLE}").df()

    report = build_report(df)
    out = reports_dir / "02_feature_summary.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {out}")
    return counts


if __name__ == "__main__":
    build()