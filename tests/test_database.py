"""Тесты SQL-запросов, ограничений, импорта и отката ПР7."""

import sqlite3
from contextlib import closing

import pytest

from db.check_queries import SAMPLE_PARAMS
from db.database import get_connection
from db.import_json import import_data
from db.queries import fetch_all, load_queries
from models import Employee, Material, SupplyRequest
from storage import save_employees, save_materials, save_requests


@pytest.fixture
def imported_database(tmp_path):
    source = tmp_path / "source"
    materials = [Material(1, "Бумага", "пачка", 10),
                 Material(2, "Маркер", "шт", 0),
                 Material(3, "Ручка", "шт", 100)]
    employees = [Employee(1, "Иванов", "ivanov@example.local", "Снабжение"),
                 Employee(2, "Петров", "petrov@example.local", "ИТ")]
    requests = [
        SupplyRequest(1, employees[0], materials[0], 2, "2026-09-20",
                      "Утверждена", ["Новая", "Утверждена"]),
        SupplyRequest(2, employees[1], materials[0], 3, "2026-09-21"),
        SupplyRequest(3, employees[0], materials[1], 1, "2026-09-20",
                      "Отменена", ["Новая", "Отменена"]),
        SupplyRequest(4, employees[0], materials[2], 10, "2026-09-20",
                      "Выполнена"),
    ]
    save_materials(source / "materials.json", materials)
    save_employees(source / "employees.json", employees)
    save_requests(source / "requests.json", requests)
    db_path = tmp_path / "test.sqlite"
    counts = import_data(source, db_path)
    assert counts == {"materials": 3, "employees": 2, "supply_requests": 4}
    return source, db_path


def test_import_preserves_rows_keys_and_history(imported_database) -> None:
    _, db_path = imported_database
    with closing(get_connection(db_path)) as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert len(conn.execute(
            "PRAGMA foreign_key_list(supply_requests)"
        ).fetchall()) == 2
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    row = fetch_all("request_detail", {"id": 1}, db_path=db_path)[0]
    assert isinstance(row, sqlite3.Row)
    assert row["employee_name"] == "Иванов"
    assert row["material_name"] == "Бумага"
    history = fetch_all("request_history", {"id": 1}, db_path=db_path)
    assert [item["status"] for item in history] == ["Новая", "Утверждена"]


def test_all_named_sql_queries_execute(imported_database) -> None:
    _, db_path = imported_database
    queries = load_queries()
    assert len(queries) >= 10
    for name in queries:
        rows = fetch_all(name, SAMPLE_PARAMS.get(name), db_path=db_path)
        assert all(isinstance(row, sqlite3.Row) for row in rows)


def test_filters_join_and_date_queries(imported_database) -> None:
    _, db_path = imported_database
    active = fetch_all("requests_active", db_path=db_path)
    assert [row["id"] for row in active] == [1, 2]
    available = fetch_all("materials_available", {"quantity": 10},
                          db_path=db_path)
    assert [row["id"] for row in available] == [1, 3]
    on_date = fetch_all("requests_on_date", {"created": "2026-09-20"},
                        db_path=db_path)
    assert [row["id"] for row in on_date] == [1, 3, 4]
    assert fetch_all("material_detail", {"id": "1 OR 1=1"},
                     db_path=db_path) == []


def test_aggregates_groups_having_and_subquery(imported_database) -> None:
    _, db_path = imported_database
    summary = fetch_all("request_summary", db_path=db_path)[0]
    assert dict(summary) == {"total": 4, "active": 2, "completed": 1}
    groups = {row["id"]: row for row in
              fetch_all("material_statistics", db_path=db_path)}
    assert groups[1]["requests_count"] == 2
    assert groups[1]["requested_quantity"] == 5
    assert groups[2]["requests_count"] == 0
    assert groups[3]["requested_quantity"] == 0
    popular = fetch_all("popular_materials", {"minimum": 1}, db_path=db_path)
    assert [row["id"] for row in popular] == [1]
    departments = fetch_all("department_statistics", {"minimum": 1},
                            db_path=db_path)
    assert departments == []
    free = fetch_all("materials_without_active", db_path=db_path)
    assert {row["id"] for row in free} == {2, 3}
    recent = fetch_all("recent_requests", {"limit": 1, "offset": 1},
                       db_path=db_path)
    assert recent[0]["id"] == 4


@pytest.mark.parametrize("sql", [
    "INSERT INTO materials VALUES (1, 'Дубликат', 'шт', 5)",
    "INSERT INTO materials VALUES (5, 'Ошибка', 'шт', -1)",
    "INSERT INTO supply_requests VALUES "
    "(99, 999, 1, 2, '2026-09-20', 'Новая')",
    "INSERT INTO supply_requests VALUES "
    "(99, 1, 1, 0, '2026-09-20', 'Новая')",
    "INSERT INTO supply_requests VALUES "
    "(99, 1, 1, 2, '2026-09-20', 'Неизвестно')",
])
def test_database_enforces_constraints(imported_database, sql) -> None:
    _, db_path = imported_database
    with closing(get_connection(db_path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            with conn:
                conn.execute(sql)


def test_reimport_requires_explicit_replace(imported_database) -> None:
    source, db_path = imported_database
    with pytest.raises(ValueError, match="--replace"):
        import_data(source, db_path)
    import_data(source, db_path, replace=True)
    assert len(fetch_all("requests_all", db_path=db_path)) == 4


def test_failed_replace_rolls_back_every_table(imported_database) -> None:
    source, db_path = imported_database
    original = [dict(row) for row in
                fetch_all("requests_all", db_path=db_path)]
    save_employees(source / "employees.json", [
        Employee(1, "Первый", "same@example.local", "Отдел"),
        Employee(2, "Второй", "same@example.local", "Отдел"),
    ])
    with pytest.raises(sqlite3.IntegrityError):
        import_data(source, db_path, replace=True)
    assert original == [dict(row) for row in
                        fetch_all("requests_all", db_path=db_path)]
    assert len(fetch_all("materials_list", db_path=db_path)) == 3
    assert len(fetch_all("request_history", {"id": 1}, db_path=db_path)) == 2


def test_missing_source_does_not_replace_database(imported_database) -> None:
    source, db_path = imported_database
    with pytest.raises(FileNotFoundError):
        import_data(source / "absent", db_path, replace=True)
    assert len(fetch_all("materials_list", db_path=db_path)) == 3


def test_read_query_does_not_create_empty_database(tmp_path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        fetch_all("materials_list", db_path=path)
    assert not path.exists()
