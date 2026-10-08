"""Тесты маршрутов и HTML-страниц Django-версии ПР5."""

import os

import django
from django.test import Client


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "consumables_service.settings",
)
django.setup()


client = Client()


def response_text(response) -> str:
    """Декодировать HTML-ответ Django для проверок."""
    return response.content.decode("utf-8")


def test_homepage_contains_navigation() -> None:
    response = client.get("/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Сервис заказа расходных материалов" in content
    assert 'href="/materials/"' in content
    assert 'href="/requests/"' in content


def test_materials_page_uses_json_data() -> None:
    response = client.get("/materials/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Бумага А4" in content
    assert "/materials/1/" in content


def test_material_detail_and_missing_material() -> None:
    response = client.get("/materials/1/")
    assert response.status_code == 200
    assert "пачка" in response_text(response)

    missing = client.get("/materials/999/")
    assert missing.status_code == 404
    assert "Материал не найден" in response_text(missing)


def test_requests_page_restores_object_links() -> None:
    response = client.get("/requests/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Иванов И.И." in content
    assert "Бумага А4" in content
    assert "/requests/1/" in content


def test_request_detail_and_missing_request() -> None:
    response = client.get("/requests/1/")
    content = response_text(response)
    assert response.status_code == 200
    assert "Административный отдел" in content
    assert "Утверждена" in content
    assert "/materials/1/" in content

    missing = client.get("/requests/999/")
    assert missing.status_code == 404
    assert "Заявка не найдена" in response_text(missing)
