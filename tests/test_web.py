"""Тесты SQL-представлений ПР7 и сохранённых шаблонов ПР6."""

import os
import sqlite3
from contextlib import closing
from types import SimpleNamespace

import django
import pytest
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import setup_test_environment
from django.urls import resolve, reverse

from db.database import get_connection
from db.import_json import import_data
from models import Employee, Material, SupplyRequest
from storage import save_employees, save_materials, save_requests


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "consumables_service.settings",
)
django.setup()
setup_test_environment()


@pytest.fixture
def client(tmp_path):
    """Изолировать веб-тесты от рабочих данных и текущего каталога."""
    data_dir = tmp_path / "data"
    material = Material(1, "Бумага А4", "пачка", 25)
    employee = Employee(
        1, "Иванов И.И.", "ivanov@example.local", "Административный отдел"
    )
    supply_request = SupplyRequest(
        1, employee, material, 5, "2026-09-20", "Утверждена"
    )
    save_materials(data_dir / "materials.json", [material])
    save_employees(data_dir / "employees.json", [employee])
    save_requests(data_dir / "requests.json", [supply_request])
    db_path = data_dir / "consumables.sqlite"
    import_data(data_dir, db_path)
    with override_settings(BASE_DIR=tmp_path, SUPPLY_DB_PATH=db_path):
        yield Client()


def change_database(tmp_path, sql, params=()) -> None:
    """Изменить изолированную базу вместо рабочих JSON-файлов."""
    db_path = tmp_path / "data" / "consumables.sqlite"
    with closing(get_connection(db_path)) as c:
        with c:
            c.execute(sql, params)


def response_text(response) -> str:
    """Декодировать HTML-ответ Django для проверок."""
    return response.content.decode("utf-8")


def test_homepage_contains_navigation(client) -> None:
    response = client.get("/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Сервис заказа расходных материалов" in content
    assert 'href="/materials/"' in content
    assert 'href="/requests/"' in content


def test_materials_page_uses_sqlite_data(client) -> None:
    response = client.get("/materials/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Бумага А4" in content
    assert "/materials/1/" in content


def test_material_detail_and_missing_material(client) -> None:
    response = client.get("/materials/1/")
    assert response.status_code == 200
    assert "пачка" in response_text(response)

    missing = client.get("/materials/999/")
    assert missing.status_code == 404
    assert "Материал не найден" in response_text(missing)


def test_requests_page_restores_object_links(client) -> None:
    response = client.get("/requests/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Иванов И.И." in content
    assert "Бумага А4" in content
    assert "/requests/1/" in content


def test_request_detail_and_missing_request(client) -> None:
    response = client.get("/requests/1/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Административный отдел" in content
    assert "Утверждена" in content
    assert "/materials/1/" in content

    missing = client.get("/requests/999/")
    assert missing.status_code == 404
    assert "Заявка не найдена" in response_text(missing)


@pytest.mark.parametrize("path", ["/materials/", "/materials/1/"])
def test_zero_stock_is_displayed(client, tmp_path, path) -> None:
    change_database(tmp_path, "UPDATE materials SET stock = 0 WHERE id = 1")
    response = client.get(path)
    assert response.status_code == 200
    assert "danger" in response_text(response)
    if path.endswith("1/"):
        assert "Нет на складе" in response_text(response)


@pytest.mark.parametrize(
    "path,filename,message",
    [
        ("/materials/", "materials.json", "Материалы пока не добавлены"),
        ("/requests/", "requests.json", "Заявки пока не созданы"),
    ],
)
def test_empty_lists(client, tmp_path, path, filename, message) -> None:
    change_database(tmp_path, "DELETE FROM supply_requests")
    if filename == "materials.json":
        change_database(tmp_path, "DELETE FROM materials")
    response = client.get(path)
    assert response.status_code == 200
    assert message in response_text(response)


@pytest.mark.parametrize(
    "path",
    ["/materials/", "/materials/1/", "/requests/", "/requests/1/"],
)
def test_database_values_are_escaped(client, tmp_path, path) -> None:
    change_database(tmp_path, "UPDATE materials SET name = ? WHERE id = 1",
                    ('<script>alert("test")</script>',))
    response = client.get(path)
    content = response_text(response)
    assert response.status_code == 200
    assert "&lt;script&gt;" in content
    assert "<script>" not in content


@pytest.mark.parametrize(
    "path,view_name",
    [
        ("/", "homepage:index"),
        ("/materials/", "inventory:materials"),
        ("/materials/1/", "inventory:material_detail"),
        ("/requests/", "supply_requests:requests"),
        ("/requests/1/", "supply_requests:request_detail"),
    ],
)
def test_named_routes(path, view_name) -> None:
    match = resolve(path)
    assert match.view_name == view_name
    assert reverse(view_name, kwargs=match.kwargs) == path


def test_viewing_pages_does_not_change_json(client, tmp_path) -> None:
    files = list((tmp_path / "data").glob("*.json"))
    before = {path: path.read_bytes() for path in files}
    for path in ("/", "/materials/", "/materials/1/",
                 "/requests/", "/requests/1/"):
        assert client.get(path).status_code == 200
    assert {path: path.read_bytes() for path in files} == before


@pytest.mark.parametrize(
    "path,template,context_key",
    [
        ("/", "homepage/index.html", None),
        ("/materials/", "inventory/material_list.html", "materials"),
        ("/materials/1/", "inventory/material_detail.html", "material"),
        ("/requests/", "supply_requests/request_list.html", "supply_requests"),
        ("/requests/1/", "supply_requests/request_detail.html",
         "supply_request"),
    ],
)
def test_templates_inheritance_and_context(
    client, path, template, context_key
) -> None:
    response = client.get(path)
    names = {item.name for item in response.templates}
    assert {template, "base.html", "includes/navigation.html"} <= names
    if context_key is not None:
        assert response.context[context_key] is not None
    if context_key == "material":
        assert isinstance(response.context[context_key], sqlite3.Row)
    if context_key == "supply_request":
        item = response.context[context_key]
        assert isinstance(item, sqlite3.Row)
        assert item["material_name"] == "Бумага А4"
        assert item["employee_name"] == "Иванов И.И."


@pytest.mark.parametrize(
    "path,template,context_key",
    [
        ("/materials/9999/", "inventory/material_detail.html", "material"),
        ("/requests/9999/", "supply_requests/request_detail.html",
         "supply_request"),
    ],
)
def test_missing_objects_are_handled_in_templates(
    client, path, template, context_key
) -> None:
    response = client.get(path)
    assert response.status_code == 404
    assert response.context[context_key] is None
    assert template in {item.name for item in response.templates}


@pytest.mark.parametrize("status", [
    "Новая", "На согласовании", "Утверждена", "В закупке",
    "Выполнена", "Отклонена", "Отменена",
])
@pytest.mark.parametrize("path", ["/requests/", "/requests/1/"])
def test_shared_status_template(client, tmp_path, status, path) -> None:
    change_database(tmp_path,
                    "UPDATE supply_requests SET status = ? WHERE id = 1",
                    (status,))
    response = client.get(path)
    names = {template.name for template in response.templates}
    assert "supply_requests/includes/request_status.html" in names
    assert status in response_text(response)
    if status == "Отменена":
        assert "request-status-cancelled" in response_text(response)


def test_filters_and_material_include(client) -> None:
    materials_response = client.get("/materials/")
    assert "Позиций: 1" in response_text(materials_response)
    assert "inventory/includes/material_card.html" in {
        template.name for template in materials_response.templates
    }
    requests_response = client.get("/requests/")
    assert "20.09.2026" in response_text(requests_response)
    unnamed = SimpleNamespace(id=1, name="", stock=0, unit="шт")
    content = render_to_string(
        "inventory/includes/material_card.html", {"material": unnamed}
    )
    assert "Без названия" in content


@pytest.mark.parametrize(
    "asset",
    ["homepage/css/style.css", "homepage/js/main.js", "homepage/img/logo.svg"],
)
def test_static_resources_are_found_and_linked(client, asset) -> None:
    assert finders.find(asset) is not None
    assert f"/static/{asset}" in response_text(client.get("/"))


@pytest.mark.parametrize("path", ["/materials/text/", "/requests/text/"])
def test_text_is_not_accepted_by_int_routes(client, path) -> None:
    assert client.get(path).status_code == 404


def test_pages_use_database_not_later_json_changes(client, tmp_path) -> None:
    save_materials(tmp_path / "data" / "materials.json",
                   [Material(1, "Только в JSON", "шт", 1)])
    change_database(tmp_path, "UPDATE materials SET name = ? WHERE id = 1",
                    ("Название из SQLite",))
    for path in ("/materials/", "/materials/1/", "/requests/", "/requests/1/"):
        content = response_text(client.get(path))
        assert "Название из SQLite" in content
        assert "Только в JSON" not in content


@pytest.mark.parametrize("quantity", ["0", "-1", "abc", "1 OR 1=1", "9" * 30])
def test_material_search_rejects_invalid_quantity(client, quantity) -> None:
    response = client.get("/materials/available/", {"quantity": quantity})
    assert response.status_code == 400


def test_available_materials_get_search(client) -> None:
    assert client.get("/materials/available/").context["searched"] is False
    found = client.get("/materials/available/", {"quantity": "25"})
    assert [row["id"] for row in found.context["materials"]] == [1]
    missing = client.get("/materials/available/", {"quantity": "26"})
    assert len(missing.context["materials"]) == 0


def test_requests_by_date(client) -> None:
    found = client.get("/requests/search/", {"date": "2026-09-20"})
    assert [row["id"] for row in found.context["supply_requests"]] == [1]
    empty = client.get("/requests/search/", {"date": "2026-09-21"})
    assert "На выбранную дату заявок нет" in response_text(empty)
    for value in ("2026-02-30", "20260920", "' OR 1=1 --"):
        response = client.get("/requests/search/", {"date": value})
        assert response.status_code == 400


def test_active_requests_and_employees(client, tmp_path) -> None:
    assert len(client.get("/requests/active/").context["supply_requests"]) == 1
    change_database(tmp_path,
                    "UPDATE supply_requests SET status = 'Отменена'")
    assert len(client.get("/requests/active/").context["supply_requests"]) == 0
    assert len(client.get("/requests/").context["supply_requests"]) == 1
    assert "Иванов И.И." in response_text(client.get("/requests/employees/"))


def test_statistics_keep_zero_request_material(client, tmp_path) -> None:
    change_database(tmp_path,
                    "INSERT INTO materials VALUES (2, 'Маркер', 'шт', 0)")
    response = client.get("/requests/statistics/")
    assert response.status_code == 200
    assert response.context["material_summary"]["total"] == 2
    assert response.context["request_summary"]["active"] == 1
    rows = {row["id"]: row for row in response.context["material_statistics"]}
    assert rows[2]["requests_count"] == 0
    assert rows[2]["requested_quantity"] == 0
    assert "Маркер" in response_text(response)
