"""Тесты JSON-хранилища объектной модели."""

import pytest

from models import Employee, Material, SupplyRequest
from storage import (
    load_employees,
    load_json,
    load_materials,
    load_requests,
    save_employees,
    save_json,
    save_materials,
    save_requests,
)


def test_save_and_load_json(tmp_path) -> None:
    filename = tmp_path / "data.json"
    expected = [{"id": 1, "name": "Бумага А4"}]
    save_json(filename, expected)
    assert load_json(filename) == expected


def test_missing_and_invalid_json(tmp_path) -> None:
    assert load_json(tmp_path / "missing.json") == []
    filename = tmp_path / "broken.json"
    filename.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="некорректный JSON"):
        load_json(filename)


def test_object_collections_round_trip(tmp_path) -> None:
    materials_file = tmp_path / "materials.json"
    employees_file = tmp_path / "employees.json"
    requests_file = tmp_path / "requests.json"
    materials = [Material(1, "Бумага А4", "пачка", 10)]
    employees = [
        Employee(1, "Иванов", "ivanov@example.local", "Снабжение")
    ]
    requests = [
        SupplyRequest(1, employees[0], materials[0], 2, "2026-09-20")
    ]

    save_materials(materials_file, materials)
    save_employees(employees_file, employees)
    save_requests(requests_file, requests)

    loaded_materials = load_materials(materials_file)
    loaded_employees = load_employees(employees_file)
    loaded_requests = load_requests(
        requests_file, loaded_materials, loaded_employees
    )

    assert isinstance(loaded_materials[0], Material)
    assert isinstance(loaded_employees[0], Employee)
    assert isinstance(loaded_requests[0], SupplyRequest)
    assert loaded_requests[0].material is loaded_materials[0]
    assert loaded_requests[0].employee is loaded_employees[0]


def test_request_with_missing_link_is_rejected(tmp_path) -> None:
    filename = tmp_path / "requests.json"
    save_json(
        filename,
        [
            {
                "id": 1,
                "employee_id": 99,
                "material_id": 1,
                "quantity": 1,
                "created": "2026-09-20",
                "status": "Новая",
                "history": ["Новая"],
            }
        ],
    )
    materials = [Material(1, "Бумага", "пачка", 10)]
    with pytest.raises(ValueError, match="не найден сотрудник"):
        load_requests(filename, materials, [])
