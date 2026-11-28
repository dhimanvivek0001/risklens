"""Phase 2: build one row of features per applicant.

Runs the SQL files in features/sql in order (01 -> 07), then checks the result.

Run:
  python -m risklens.features.build
"""

import time
from pathlib import Path

import duckdb

from risklens import PROJECT_ROOT, load_settings

SQL_DIR = Path(__file__).parent / "sql"
FINAL_TABLE = "features.application_features"


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


def build(db_file=None):
    """Run the whole Phase 2 pipeline on the project database."""
    settings = load_settings()
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]

    with duckdb.connect(str(db_file)) as con:
        run_sql_files(con)
        counts = quality_checks(con)
    return counts


if __name__ == "__main__":
    build()