"""Load every Home Credit CSV into a local DuckDB warehouse (schema `raw`).

DuckDB reads CSVs directly and is fast enough for the 27M-row tables on a laptop.

Run:
  python -m risklens.data.load
"""

import duckdb
import pandas as pd

from risklens import PROJECT_ROOT, load_settings

SKIP = {"sample_submission"}                       # Kaggle submission template, not data
NON_UTF8 = {"homecredit_columns_description"}     # data dictionary saved as Windows-1252


def load_raw(raw_dir=None, db_file=None) -> dict[str, int]:
    """Create one raw.<table> per CSV. Returns {table_name: row_count}."""
    settings = load_settings()
    raw_dir = raw_dir or PROJECT_ROOT / settings["paths"]["raw_dir"]
    db_file = db_file or PROJECT_ROOT / settings["paths"]["duckdb_file"]
    db_file.parent.mkdir(parents=True, exist_ok=True)

    csvs = sorted(raw_dir.glob("*.csv"), key=lambda p: p.name.lower())
    if not csvs:
        raise FileNotFoundError(f"No CSV files in {raw_dir}. Run risklens.data.download first.")

    counts: dict[str, int] = {}
    with duckdb.connect(str(db_file)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw").fetchall()
        for csv in csvs:
            table = csv.stem.lower()
            if table in SKIP:
                continue
            if table in NON_UTF8:
                df = pd.read_csv(csv, encoding="cp1252")
                con.register("tmp_df", df)
                con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM tmp_df").fetchall()
                con.unregister("tmp_df")
            else:
                con.execute(
                    f"CREATE OR REPLACE TABLE raw.{table} AS "
                    f"SELECT * FROM read_csv_auto(?, sample_size=-1)",
                    [str(csv)],
                ).fetchall()
            counts[table] = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchall()[0][0]
            print(f"raw.{table:<32} {counts[table]:>12,} rows")
    return counts


if __name__ == "__main__":
    load_raw()
