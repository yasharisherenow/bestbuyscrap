from pathlib import Path

from src.state_manager import load_json, load_watchlist, save_json


def test_load_json_missing_returns_default(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    assert load_json(path, {"a": 1}) == {"a": 1}


def test_save_and_load_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    data = {"x": {"price": "100"}}
    save_json(path, data)
    loaded = load_json(path, {})
    assert loaded == data


def test_load_watchlist_normalizes_values(tmp_path: Path) -> None:
    path = tmp_path / "watchlist.json"
    save_json(path, {"skus": [" 123 ", ""], "keywords": [" RTX ", ""]})

    watchlist = load_watchlist(path)

    assert watchlist["skus"] == ["123"]
    assert watchlist["keywords"] == ["rtx"]
