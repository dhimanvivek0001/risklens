"""Download the Home Credit competition files with the Kaggle API.

Before running:
  1. Create a Kaggle account and accept the competition rules at
     https://www.kaggle.com/competitions/home-credit-default-risk/rules
  2. Kaggle -> Settings -> API -> "Create New Token" -> save kaggle.json to
     C:\\Users\\<you>\\.kaggle\\kaggle.json  (Windows) or ~/.kaggle/kaggle.json

Run:
  python -m risklens.data.download
"""

import subprocess
import sys
import zipfile

from risklens import PROJECT_ROOT, load_settings


def main() -> None:
    settings = load_settings()
    competition = settings["kaggle"]["credit_competition"]
    raw_dir = PROJECT_ROOT / settings["paths"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {competition} to {raw_dir} ...")
    result = subprocess.run(
        ["kaggle", "competitions", "download", "-c", competition, "-p", str(raw_dir)],
        check=False,
    )
    if result.returncode != 0:
        sys.exit("Download failed. Check kaggle.json and that you accepted the competition rules.")

    for zip_path in raw_dir.glob("*.zip"):
        print(f"Unzipping {zip_path.name} ...")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(raw_dir)
        zip_path.unlink()

    csvs = sorted(p.name for p in raw_dir.glob("*.csv"))
    print(f"Done. {len(csvs)} CSV files: {', '.join(csvs)}")


if __name__ == "__main__":
    main()
