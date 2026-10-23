"""Выполнение именованных запросов из единого SQL-файла."""

import re
import sqlite3
from contextlib import closing
from functools import lru_cache
from typing import Optional

from db.database import BASE_DIR, PathLike, get_connection


@lru_cache(maxsize=1)
def load_queries() -> dict[str, str]:
    """Прочитать SQL с разделителями -- name: имя_запроса."""
    sql = (BASE_DIR / "sql" / "queries.sql").read_text(encoding="utf-8")
    parts = re.split(r"(?m)^-- name: (\w+)\s*$", sql)
    return {parts[i]: parts[i + 1].strip()
            for i in range(1, len(parts), 2)}


def fetch_all(
    name: str,
    params: Optional[dict] = None,
    *,
    db_path: Optional[PathLike] = None,
) -> list[sqlite3.Row]:
    """Выполнить один SELECT с отдельной передачей значений параметров."""
    sql = load_queries()[name]
    with closing(get_connection(db_path, readonly=True)) as conn:
        return conn.execute(sql, params or {}).fetchall()
