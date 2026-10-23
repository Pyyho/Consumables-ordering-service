"""Транзакционный импорт исходных JSON-данных в SQLite."""

import argparse
from contextlib import closing
from pathlib import Path
from typing import Optional

from db.database import BASE_DIR, DB_PATH, PathLike
from db.database import get_connection, initialize_database
from storage import load_employees, load_materials, load_requests


def import_data(
    data_dir: Optional[PathLike] = None,
    db_path: Optional[PathLike] = None,
    *,
    replace: bool = False,
) -> dict[str, int]:
    """Импортировать объекты; при ошибке откатить всю транзакцию."""
    source = Path(data_dir) if data_dir is not None else BASE_DIR / "data"
    for filename in ("materials.json", "employees.json", "requests.json"):
        if not (source / filename).is_file():
            raise FileNotFoundError(source / filename)
    materials = load_materials(source / "materials.json")
    employees = load_employees(source / "employees.json")
    requests = load_requests(source / "requests.json", materials, employees)
    initialize_database(db_path)
    with closing(get_connection(db_path)) as conn:
        with conn:
            occupied = conn.execute(
                "SELECT (SELECT COUNT(*) FROM materials) + "
                "(SELECT COUNT(*) FROM employees) + "
                "(SELECT COUNT(*) FROM supply_requests)"
            ).fetchone()[0]
            if occupied and not replace:
                raise ValueError(
                    "База уже содержит данные. Для явной замены "
                    "используйте --replace."
                )
            if replace:
                conn.execute("DELETE FROM request_history")
                conn.execute("DELETE FROM supply_requests")
                conn.execute("DELETE FROM employees")
                conn.execute("DELETE FROM materials")
            conn.executemany(
                "INSERT INTO materials (id, name, unit, stock) "
                "VALUES (?, ?, ?, ?)",
                [(m.id, m.name, m.unit, m.stock) for m in materials],
            )
            conn.executemany(
                "INSERT INTO employees (id, name, email, department) "
                "VALUES (?, ?, ?, ?)",
                [(e.id, e.name, e.email, e.department) for e in employees],
            )
            conn.executemany(
                "INSERT INTO supply_requests "
                "(id, material_id, employee_id, quantity, created, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(r.id, r.material.id, r.employee.id, r.quantity,
                  r.created.isoformat(), r.status) for r in requests],
            )
            conn.executemany(
                "INSERT INTO request_history "
                "(request_id, position, status) VALUES (?, ?, ?)",
                [(r.id, position, status) for r in requests
                 for position, status in enumerate(r.history)],
            )
    return {"materials": len(materials), "employees": len(employees),
            "supply_requests": len(requests)}


def main() -> None:
    """Разобрать параметры и выполнить импорт."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true",
                        help="заменить содержимое предметных таблиц из JSON")
    args = parser.parse_args()
    result = import_data(replace=args.replace)
    print(f"Импорт в {DB_PATH}: {result}")


if __name__ == "__main__":
    main()
