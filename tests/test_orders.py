"""Тесты функций обработки заявок."""

from datetime import date

import pytest

from orders import (
    cancel_request,
    change_status,
    create_request,
    filter_requests,
    show_history,
)


def sample_materials() -> list[dict]:
    """Вернуть тестовый справочник материалов."""
    return [
        {"id": 1, "name": "Бумага А4", "unit": "пачка", "stock": 10}
    ]


def test_create_request() -> None:
    requests = []
    request = create_request(
        requests,
        sample_materials(),
        "Иванов И.И.",
        1,
        2,
        date(2026, 9, 20),
    )
    assert request["id"] == 1
    assert request["created"] == "2026-09-20"
    assert request["status"] == "Новая"


def test_create_request_rejects_insufficient_stock() -> None:
    with pytest.raises(ValueError, match="недостаточно"):
        create_request([], sample_materials(), "Иванов", 1, 20)


def test_change_status_updates_history() -> None:
    requests = []
    create_request(requests, sample_materials(), "Иванов", 1, 2)
    change_status(requests, 1, "На согласовании")
    assert requests[0]["history"] == ["Новая", "На согласовании"]


def test_filter_requests_by_employee_and_status() -> None:
    requests = []
    create_request(requests, sample_materials(), "Иванов", 1, 2)
    create_request(requests, sample_materials(), "Петров", 1, 1)
    selected = filter_requests(
        requests, status="Новая", employee="иван"
    )
    assert [request["employee"] for request in selected] == ["Иванов"]


def test_cancel_request_and_show_history() -> None:
    requests = []
    create_request(requests, sample_materials(), "Иванов", 1, 2)
    cancel_request(requests, 1)
    assert requests[0]["status"] == "Отменена"
    assert show_history(requests, 1).endswith("Новая → Отменена")
