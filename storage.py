"""Загрузка и сохранение данных проекта в JSON-файлах."""

import json
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def load_json(filename: PathLike) -> list[dict]:
    """Загрузить список словарей; для отсутствующего файла вернуть []."""
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"файл {path} содержит некорректный JSON") from error

    if not isinstance(data, list):
        raise ValueError(f"в файле {path} ожидался список")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"в файле {path} ожидался список объектов")
    return data


def save_json(filename: PathLike, data: list[dict]) -> None:
    """Сохранить список словарей в JSON с помощью контекстного менеджера."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_materials(filename: PathLike) -> list[dict]:
    """Загрузить справочник материалов."""
    return load_json(filename)


def save_materials(filename: PathLike, materials: list[dict]) -> None:
    """Сохранить справочник материалов."""
    save_json(filename, materials)


def load_requests(filename: PathLike) -> list[dict]:
    """Загрузить заявки."""
    return load_json(filename)


def save_requests(filename: PathLike, requests: list[dict]) -> None:
    """Сохранить заявки."""
    save_json(filename, requests)
