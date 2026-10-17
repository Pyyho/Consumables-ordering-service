"""Тесты маршрутов, шаблонов и статических ресурсов ПР6."""

import os
from types import SimpleNamespace

import django
import pytest
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import setup_test_environment
from django.urls import resolve, reverse

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
    with override_settings(BASE_DIR=tmp_path):
        yield Client()


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


def test_materials_page_uses_json_data(client) -> None:
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
    save_materials(
        tmp_path / "data" / "materials.json",
        [Material(1, "Бумага А4", "пачка", 0)],
    )
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
    (tmp_path / "data" / filename).write_text("[]", encoding="utf-8")
    response = client.get(path)
    assert response.status_code == 200
    assert message in response_text(response)


@pytest.mark.parametrize(
    "path",
    ["/materials/", "/materials/1/", "/requests/", "/requests/1/"],
)
def test_json_values_are_escaped(client, tmp_path, path) -> None:
    save_materials(
        tmp_path / "data" / "materials.json",
        [Material(1, '<script>alert("test")</script>', "шт", 25)],
    )
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
        assert isinstance(response.context[context_key], Material)
    if context_key == "supply_request":
        item = response.context[context_key]
        assert isinstance(item, SupplyRequest)
        assert isinstance(item.material, Material)
        assert isinstance(item.employee, Employee)


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
    material = Material(1, "Бумага А4", "пачка", 25)
    employee = Employee(1, "Иванов", "ivanov@example.local", "Снабжение")
    item = SupplyRequest(1, employee, material, 2, "2026-09-20", status)
    save_requests(tmp_path / "data" / "requests.json", [item])
    response = client.get(path)
    names = {template.name for template in response.templates}
    assert "supply_requests/includes/request_status.html" in names
    assert status in response_text(response)
    if item.is_cancelled:
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
