"""Соединения и создание отдельной предметной базы SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional, Union


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "consumables.sqlite"
PathLike = Union[str, Path]


def get_connection(
    db_path: Optional[PathLike] = None, *, readonly: bool = False
) -> sqlite3.Connection:
    """Открыть соединение с Row и проверкой FK; закрывает вызывающий код."""
    path = Path(db_path) if db_path is not None else DB_PATH
    if readonly:
        conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: Optional[PathLike] = None) -> None:
    """Создать таблицы без удаления существующих данных."""
    schema = (BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8")
    with closing(get_connection(db_path)) as conn:
        conn.executescript(schema)
        conn.commit()


if __name__ == "__main__":
    initialize_database()
    print(f"Схема создана: {DB_PATH}")
