"""Тесты класса SupplyRequest и функций обработки заявок."""

from datetime import date

import pytest

from models import Employee, Material, SupplyRequest
from models.requests import (
    cancel_request,
    change_status,
    create_request,
    filter_requests,
    show_history,
    sort_requests,
)


def sample_objects() -> tuple[Employee, Material]:
    """Вернуть связанные объекты для тестов заявок."""
    employee = Employee(
        1,
        "Иванов И.И.",
        "ivanov@example.local",
        "Снабжение",
    )
    material = Material(1, "Бумага А4", "пачка", 10)
    return employee, material


def test_request_creation_and_links() -> None:
    employee, material = sample_objects()
    request = SupplyRequest(
        1, employee, material, 2, date(2026, 9, 20)
    )
    assert request.employee is employee
    assert request.material is material
    assert request.status == "Новая"
    assert "Бумага А4" in str(request)


def test_request_from_data_restores_state() -> None:
    employee, material = sample_objects()
    request = SupplyRequest.from_data(
        {
            "id": 1,
            "quantity": 2,
            "created": "2026-09-20",
            "status": "Утверждена",
            "history": ["Новая", "Утверждена"],
        },
        employee,
        material,
    )
    assert request.status == "Утверждена"
    assert request.history == ("Новая", "Утверждена")


def test_create_request_adds_object() -> None:
    employee, material = sample_objects()
    requests = []
    request = create_request(
        requests,
        employee,
        material,
        2,
        date(2026, 9, 20),
    )
    assert requests == [request]
    assert request.created == date(2026, 9, 20)


def test_create_request_rejects_insufficient_stock() -> None:
    employee, material = sample_objects()
    with pytest.raises(ValueError, match="недостаточно"):
        create_request([], employee, material, 20)


def test_change_status_updates_encapsulated_history() -> None:
    employee, material = sample_objects()
    requests = [SupplyRequest(1, employee, material, 2, "2026-09-20")]
    change_status(requests, 1, "На согласовании")
    assert requests[0].status == "На согласовании"
    assert requests[0].history == ("Новая", "На согласовании")


def test_cancel_request_changes_state_without_deleting() -> None:
    employee, material = sample_objects()
    requests = [SupplyRequest(1, employee, material, 2, "2026-09-20")]
    cancel_request(requests, 1)
    assert len(requests) == 1
    assert requests[0].is_cancelled
    assert show_history(requests, 1).endswith("Новая → Отменена")


def test_filter_and_sort_requests() -> None:
    employee, material = sample_objects()
    other = Employee(
        2,
        "Петрова А.С.",
        "petrova@example.local",
        "Бухгалтерия",
    )
    requests = [
        SupplyRequest(2, other, material, 1, "2026-09-21"),
        SupplyRequest(1, employee, material, 2, "2026-09-20"),
    ]
    selected = filter_requests(requests, employee="иванов")
    assert [request.id for request in selected] == [1]
    sorted_items = sort_requests(requests, by="created")
    assert [request.id for request in sorted_items] == [1, 2]
