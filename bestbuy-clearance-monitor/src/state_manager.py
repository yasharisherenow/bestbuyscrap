"""JSON state persistence utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    """Load JSON file, returning default if missing or invalid."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, value: Any) -> None:
    """Save JSON file atomically and create directories when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    tmp_path.replace(path)


def load_watchlist(path: Path) -> dict[str, list[str]]:
    """Load watchlist config with skus and keywords arrays."""
    data = load_json(path, {"skus": [], "keywords": []})
    skus = data.get("skus", []) if isinstance(data, dict) else []
    keywords = data.get("keywords", []) if isinstance(data, dict) else []
    return {
        "skus": [str(item).strip() for item in skus if str(item).strip()],
        "keywords": [str(item).strip().lower() for item in keywords if str(item).strip()],
    }


def append_log(path: Path, entry: str) -> None:
    """Append a single-line log entry to a text file, creating parent folders.

    Each run can record status data; callers should include a timestamp.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(entry + "\n")
