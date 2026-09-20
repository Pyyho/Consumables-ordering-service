"""Тесты сохранения и загрузки JSON-данных."""

import pytest

from storage import load_json, save_json


def test_save_and_load_json(tmp_path) -> None:
    filename = tmp_path / "data.json"
    expected = [{"id": 1, "name": "Бумага А4"}]
    save_json(filename, expected)
    assert load_json(filename) == expected


def test_missing_json_returns_empty_list(tmp_path) -> None:
    assert load_json(tmp_path / "missing.json") == []


def test_invalid_json_raises_value_error(tmp_path) -> None:
    filename = tmp_path / "broken.json"
    filename.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="некорректный JSON"):
        load_json(filename)
