"""RiskLens — credit and fraud decisioning engine."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_settings(path: Path | None = None) -> dict:
    """Read config/settings.yaml and return it as a dict."""
    path = path or PROJECT_ROOT / "config" / "settings.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
