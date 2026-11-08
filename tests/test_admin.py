"""Проверки сохранения истории и доступа к административной панели."""

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.urls import reverse

from inventory.models import Material
from staff.models import Employee
from supply_requests.models import RequestStatus, SupplyRequest


pytestmark = pytest.mark.django_db


def test_admin_request_history(admin_client):
    material = Material.objects.create(name="Бумага", unit="шт", stock=10)
    employee = Employee.objects.create(
        name="Иванов", email="test@example.org", department="Склад",
    )
    data = {
        "material": material.pk, "employee": employee.pk,
        "quantity": 2, "created": "2026-11-08", "status": RequestStatus.NEW,
    }
    add = reverse("admin:supply_requests_supplyrequest_add")
    response = admin_client.post(add, {**data, "quantity": 11})
    assert response.status_code == 200
    assert not SupplyRequest.objects.exists()
    assert admin_client.post(add, data).status_code == 302
    item = SupplyRequest.objects.get()
    change = reverse(
        "admin:supply_requests_supplyrequest_change", args=[item.pk]
    )
    data["status"] = RequestStatus.APPROVED
    assert admin_client.post(change, data).status_code == 302

    material_url = reverse(
        "admin:inventory_material_change", args=[material.pk]
    )
    response = admin_client.get(material_url)
    inline, = response.context["inline_admin_formsets"]
    assert inline.formset.total_form_count() == 1

    listing = reverse("admin:supply_requests_supplyrequest_changelist")
    response = admin_client.get(listing, {"q": "test@example.org"})
    assert list(response.context["cl"].result_list) == [item]
    assert admin_client.post(listing, {
        "action": "cancel_selected", "_selected_action": [item.pk],
    }).status_code == 302
    item.refresh_from_db()
    assert item.status == RequestStatus.CANCELLED
    assert list(item.status_events.values_list("status", flat=True)) == [
        RequestStatus.NEW, RequestStatus.APPROVED, RequestStatus.CANCELLED,
    ]
    assert not SupplyRequest.objects.active().exists()


def test_admin_group_can_view_but_not_create(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="reader", is_staff=True,
    )
    group = Group.objects.create(name="Просмотр каталога")
    group.permissions.add(Permission.objects.get(codename="view_material"))
    user.groups.add(group)
    client.force_login(user)
    listing = reverse("admin:inventory_material_changelist")
    assert client.get(listing).status_code == 200
    add = reverse("admin:inventory_material_add")
    assert client.get(add).status_code == 403


def test_fixture_slug_and_generated_stock(client):
    call_command("loaddata", "fixtures/pr9_initial.json", verbosity=0)
    item = Material.objects.get(pk=1)
    assert item.in_stock
    assert client.get(item.get_absolute_url()).status_code == 200
    assert client.get(f"/materials/{item.pk}/").status_code == 200
    assert client.get("/materials/missing-slug/").status_code == 404
    Material.objects.filter(pk=item.pk).update(stock=0)
    item.refresh_from_db()
    assert not item.in_stock
