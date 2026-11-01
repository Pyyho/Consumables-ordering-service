"""ПР9: перенос, CRUD, связи, запросы, фильтры и пагинация."""

import json
from contextlib import closing
from datetime import date
from hashlib import sha256
from io import StringIO

import pytest
from django.core import management
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from django.db.models.deletion import ProtectedError
from django.test.utils import CaptureQueriesContext

from db.database import get_connection
from db.import_json import import_data
from db.import_sqlite_to_orm import import_source
from inventory.models import Material
from models import Employee as LegacyEmployee
from models import Material as LegacyMaterial
from models import SupplyRequest as LegacyRequest
from staff.models import Employee
from storage import save_employees, save_materials, save_requests
from supply_requests.models import RequestHistory, SupplyRequest


pytestmark = pytest.mark.django_db


@pytest.fixture
def objects():
    material = Material.objects.create(
        name="Бумага А4", unit="пачка", stock=25
    )
    employee = Employee.objects.create(
        name="Анна", email="anna@example.local", department="Снабжение"
    )
    item = SupplyRequest.create_for(employee, material, 5, date(2026, 9, 20))
    return material, employee, item


@pytest.fixture
def source(tmp_path):
    data = tmp_path / "json"
    material = LegacyMaterial(10, "Источник", "шт", 20)
    employee = LegacyEmployee(12, "Иванов", "ivanov@example.local", "ИТ")
    item = LegacyRequest(15, employee, material, 2, "2026-09-20",
                         "Утверждена", ["Новая", "Утверждена"])
    save_materials(data / "materials.json", [material])
    save_employees(data / "employees.json", [employee])
    save_requests(data / "requests.json", [item])
    path = tmp_path / "source.sqlite"
    import_data(data, path)
    return path


def test_import_preserves_ids_dates_relations_and_source(source):
    before = sha256(source.read_bytes()).hexdigest()
    result = import_source(source, backup=False)
    assert result == {"materials": 1, "employees": 1,
                      "supply_requests": 1, "request_history": 2}
    item = SupplyRequest.objects.select_related("material", "employee").get(
        pk=15
    )
    assert item.material.pk == 10 and item.employee.pk == 12
    assert item.created == date(2026, 9, 20)
    assert item.status == "Утверждена"
    assert list(item.status_events.values_list("status", flat=True)) == [
        "Новая", "Утверждена"
    ]
    assert before == sha256(source.read_bytes()).hexdigest()


def test_import_repeat_updates_without_duplicates_or_deleting_extra(source):
    import_source(source, backup=False)
    extra = Material.objects.create(
        name="Добавлен вручную", unit="шт", stock=1
    )
    import_source(source, backup=False)
    assert Material.objects.count() == 2
    assert SupplyRequest.objects.count() == 1
    assert RequestHistory.objects.count() == 2
    assert Material.objects.filter(pk=extra.pk).exists()


def test_import_rolls_back_on_invalid_date(source):
    import_source(source, backup=False)
    with closing(get_connection(source)) as conn:
        with conn:
            conn.execute("UPDATE materials SET name = 'Не сохранять'")
            conn.execute("UPDATE supply_requests SET created = '2026-02-30'")
    with pytest.raises(ValueError):
        import_source(source, backup=False)
    assert Material.objects.get(pk=10).name == "Источник"
    assert SupplyRequest.objects.get(pk=15).created == date(2026, 9, 20)


def test_orm_crud_and_get_behavior(objects):
    material, _, _ = objects
    created = Material.objects.create(name="Маркер", unit="шт", stock=4)
    Material.objects.filter(pk=created.pk).update(stock=F("stock") + 2)
    created.refresh_from_db()
    assert created.stock == 6
    assert Material.objects.exclude(pk=material.pk).get() == created
    created.delete()
    with pytest.raises(Material.DoesNotExist):
        Material.objects.get(pk=created.pk)
    Material.objects.create(name="Другой", unit="шт", stock=1)
    with pytest.raises(Material.MultipleObjectsReturned):
        Material.objects.get(unit__in=["шт", "пачка"])


def test_protected_relations_and_history_cascade(objects):
    material, employee, item = objects
    assert list(material.supply_requests.all()) == [item]
    assert list(employee.supply_requests.all()) == [item]
    with pytest.raises(ProtectedError):
        material.delete()
    with pytest.raises(ProtectedError):
        employee.delete()
    item.delete()
    assert RequestHistory.objects.count() == 0
    material.delete()
    employee.delete()


def test_cancel_persists_and_appends_history_once(objects):
    _, _, item = objects
    item.change_status("На согласовании")
    item.change_status("На согласовании")
    item.cancel()
    item.refresh_from_db()
    assert item.is_cancelled
    assert list(item.status_events.values_list("status", flat=True)) == [
        "Новая", "На согласовании", "Отменена"
    ]
    with pytest.raises(ValueError):
        item.cancel()
    assert not SupplyRequest.objects.active().exists()


def test_create_for_checks_stock_and_model_validation(objects):
    material, employee, _ = objects
    with pytest.raises(ValueError, match="недостаточно"):
        SupplyRequest.create_for(employee, material, 100)
    invalid = SupplyRequest(material=material, employee=employee, quantity=0)
    with pytest.raises(ValidationError):
        invalid.full_clean()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            SupplyRequest.objects.create(
                material=material, employee=employee, quantity=0
            )
    assert SupplyRequest.objects.count() == 1


def test_select_related_loads_objects_in_one_query(objects):
    with CaptureQueriesContext(connection) as queries:
        result = [(r.material.name, r.employee.name) for r in
                  SupplyRequest.objects.select_related("material", "employee")]
    assert result == [("Бумага А4", "Анна")]
    assert len(queries) == 1


def test_filter_date_material_employee_status_and_search(client, objects):
    material, employee, item = objects
    other = Material.objects.create(name="Картридж", unit="шт", stock=10)
    SupplyRequest.create_for(employee, other, 2, date(2026, 9, 21))
    params = {"date": "2026-09-20", "material": material.pk,
              "employee": employee.pk, "status": "Новая", "q": "Анна"}
    response = client.get("/requests/", params)
    assert response.status_code == 200
    assert [r.pk for r in response.context["supply_requests"]] == [item.pk]
    params["material"] = other.pk
    response = client.get("/requests/", params)
    assert len(response.context["supply_requests"]) == 0


@pytest.mark.parametrize("params", [
    {"date": "2026-02-30"}, {"material": "abc"}, {"employee": "-1"},
    {"status": "unknown"}, {"material": "9" * 30},
])
def test_bad_filters_return_400(client, objects, params):
    response = client.get("/requests/", params)
    assert response.status_code == 400
    assert response.context["error"]
    assert len(response.context["supply_requests"]) == 0


@pytest.mark.parametrize("sort", ["date", "newest", "material", "employee"])
def test_sort_uses_allowed_fields_and_stable_id(client, objects, sort):
    _, employee, first = objects
    other = Material.objects.create(name="Альбом", unit="шт", stock=10)
    second = SupplyRequest.create_for(employee, other, 1, date(2026, 9, 21))
    response = client.get("/requests/", {"sort": sort})
    ids = [r.pk for r in response.context["supply_requests"]]
    expected = [second.pk, first.pk] if sort in ("newest", "material") else [
        first.pk, second.pk
    ]
    assert ids == expected
    fallback = client.get("/requests/", {"sort": "unknown_field"})
    assert fallback.context["sort"] == "date"


def test_pagination_keeps_filters_and_sort(client, objects):
    material, employee, _ = objects
    SupplyRequest.objects.bulk_create([
        SupplyRequest(material=material, employee=employee, quantity=1,
                      created=date(2026, 9, 20)) for _ in range(7)
    ])
    params = {"material": material.pk, "employee": employee.pk,
              "date": "2026-09-20", "sort": "newest", "q": "Анна"}
    response = client.get("/requests/", params)
    page = response.context["page_obj"]
    assert page.paginator.count == 8 and len(page) == 5
    content = response.content.decode()
    assert "page=2" in content and f"material={material.pk}" in content
    assert "sort=newest" in content
    second = client.get("/requests/", {**params, "page": 2})
    assert len(second.context["supply_requests"]) == 3
    invalid = client.get("/requests/", {**params, "page": "abc"})
    assert invalid.context["page_obj"].number == 1
    beyond = client.get("/requests/", {**params, "page": 999})
    assert beyond.context["page_obj"].number == 2


def test_statistics_keep_zero_counts_and_final_status_rules(client, objects):
    material, employee, item = objects
    zero = Material.objects.create(name="Без заявок", unit="шт", stock=0)
    SupplyRequest.create_for(employee, material, 3)
    item.cancel()
    response = client.get("/requests/statistics/")
    rows = {r.pk: r for r in response.context["material_statistics"]}
    assert rows[zero.pk].requests_count == 0
    assert rows[zero.pk].requested_quantity == 0
    assert rows[material.pk].requested_quantity == 3
    assert rows[material.pk].average_quantity == 3
    assert response.context["request_summary"]["active"] == 1


def test_fixture_dump_and_load(objects, tmp_path):
    stream = StringIO()
    management.call_command(
        "dumpdata", "inventory", "staff", "supply_requests", stdout=stream
    )
    assert len(json.loads(stream.getvalue())) == 4
    path = tmp_path / "fixture.json"
    path.write_text(stream.getvalue(), encoding="utf-8")
    SupplyRequest.objects.all().delete()
    Material.objects.all().delete()
    Employee.objects.all().delete()
    management.call_command("loaddata", str(path), verbosity=0)
    item = SupplyRequest.objects.get()
    assert item.material.name == "Бумага А4"
    assert item.employee.name == "Анна"
    assert item.status_events.count() == 1
