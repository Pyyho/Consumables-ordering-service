"""ПР9: проверка схемы и содержимого исходной SQLite ПР7 без записи."""

import sys
from contextlib import closing
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import DB_PATH, get_connection  # noqa: E402


def inspect_source(source=DB_PATH) -> dict:
    with closing(get_connection(source, readonly=True)) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        result = {}
        for row in tables:
            name = row["name"]
            quoted = '"' + name.replace('"', '""') + '"'
            result[name] = {
                "columns": [dict(item) for item in
                            conn.execute(f"PRAGMA table_info({quoted})")],
                "count": conn.execute(
                    f"SELECT COUNT(*) FROM {quoted}"
                ).fetchone()[0],
            }
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Исходная база содержит нарушения связей.")
        return result


if __name__ == "__main__":
    for table_name, details in inspect_source().items():
        print(table_name, details)
