"""Перенос ПР7 в таблицы ORM с сохранением ID, связей и истории."""

import argparse
import os
import sqlite3
import sys
from contextlib import closing
from datetime import date, datetime
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import BASE_DIR, get_connection  # noqa: E402


def import_source(source=None, *, backup=True) -> dict[str, int]:
    """Обновить по исходным PK; при ошибке откатить весь перенос."""
    from django.conf import settings
    from django.db import connection, transaction

    from inventory.models import Material
    from staff.models import Employee
    from supply_requests.models import RequestHistory, SupplyRequest

    source = Path(source or settings.SUPPLY_DB_PATH).resolve()
    target_name = str(connection.settings_dict["NAME"])
    if not source.is_file():
        raise FileNotFoundError(source)
    if not target_name.startswith("file:") and target_name != ":memory:":
        if Path(target_name).resolve() == source:
            raise ValueError("Источник и целевая база должны различаться.")

    with closing(get_connection(source, readonly=True)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Нарушена целостность исходной базы.")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("В исходной базе нарушены внешние ключи.")
        if backup:
            backup_dir = BASE_DIR / "data" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_path = backup_dir / f"consumables_pr9_{stamp}.sqlite"
            with closing(sqlite3.connect(backup_path)) as copy:
                conn.backup(copy)
            print(f"Резервная копия: {backup_path}")
        materials = conn.execute(
            "SELECT * FROM materials ORDER BY id"
        ).fetchall()
        employees = conn.execute(
            "SELECT * FROM employees ORDER BY id"
        ).fetchall()
        requests = conn.execute(
            "SELECT * FROM supply_requests ORDER BY id"
        ).fetchall()
        events = conn.execute(
            "SELECT * FROM request_history ORDER BY request_id, position"
        ).fetchall()

    with transaction.atomic():
        for row in materials:
            item, _ = Material.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "unit": row["unit"],
                          "stock": row["stock"]},
            )
            item.full_clean()
        for row in employees:
            item, _ = Employee.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"], "email": row["email"],
                          "department": row["department"]},
            )
            item.full_clean()
        for row in requests:
            item, _ = SupplyRequest.objects.update_or_create(
                pk=row["id"],
                defaults={"material_id": row["material_id"],
                          "employee_id": row["employee_id"],
                          "quantity": row["quantity"],
                          "created": date.fromisoformat(row["created"]),
                          "status": row["status"]},
            )
            item.full_clean()
        for row in events:
            item, _ = RequestHistory.objects.update_or_create(
                request_id=row["request_id"], position=row["position"],
                defaults={"status": row["status"]},
            )
            item.full_clean()
    return {"materials": len(materials), "employees": len(employees),
            "supply_requests": len(requests), "request_history": len(events)}


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "consumables_service.settings")
    import django

    django.setup()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    print("Перенесено:", import_source(args.source))


if __name__ == "__main__":
    main()
