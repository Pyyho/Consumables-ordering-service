"""Проверки создания, редактирования, отмены и загрузки фото."""

from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone
from PIL import Image

from inventory.models import Material
from staff.models import Employee
from supply_requests.models import RequestStatus, SupplyRequest


@pytest.fixture
def form_data(admin_client):
    material = Material.objects.create(name="Бумага", unit="шт", stock=10)
    employee = Employee.objects.create(
        name="Анна", email="anna@example.org", department="Закупки"
    )
    return {
        "material": material.pk,
        "employee": employee.pk,
        "quantity": 3,
        "created": timezone.localdate().isoformat(),
    }


@pytest.mark.parametrize(("field", "value", "message"), [
    ("quantity", 11, "На складе недостаточно материала."),
    ("quantity", 0, None),
    ("created", "2000-01-01", "Дата заявки не может быть в прошлом."),
    ("employee", "", None),
])
def test_create_rejects_invalid_input(admin_client, form_data, field, value,
                                      message):
    response = admin_client.post("/requests/new/", {**form_data, field: value})
    assert response.status_code == 200
    assert field in response.context["form"].errors
    if message:
        assert message in response.context["form"].errors[field]
    assert not SupplyRequest.objects.exists()


def test_request_workflow(admin_client, form_data):
    response = admin_client.post("/requests/new/", form_data)
    item = SupplyRequest.objects.get()
    detail = f"/requests/{item.pk}/"
    assert response.url == detail
    assert list(item.status_events.values_list("status", flat=True)) == [
        RequestStatus.NEW,
    ]
    assert admin_client.get(f"{detail}edit/").context["form"].instance == item
    response = admin_client.post(
        f"{detail}edit/", {**form_data, "quantity": 12}
    )
    assert "quantity" in response.context["form"].errors
    item.refresh_from_db()
    assert item.quantity == 3
    response = admin_client.post(
        f"{detail}edit/", {**form_data, "quantity": 5}
    )
    assert response.url == detail
    item.refresh_from_db()
    assert item.quantity == 5
    assert admin_client.get(f"{detail}cancel/").status_code == 405
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(response.wsgi_request.user)
    assert csrf_client.post(f"{detail}cancel/").status_code == 403
    response = admin_client.post(f"{detail}cancel/")
    assert response.url == detail
    item.refresh_from_db()
    assert item.is_cancelled
    assert item.status_events.last().status == RequestStatus.CANCELLED
    assert admin_client.post(f"{detail}edit/", form_data).status_code == 409
    assert admin_client.get("/requests/999999/edit/").status_code == 404


def test_edit_preserves_an_existing_past_date(admin_client, form_data):
    yesterday = timezone.localdate() - timedelta(days=1)
    item = SupplyRequest.objects.create(
        material_id=form_data["material"], employee_id=form_data["employee"],
        quantity=2, created=yesterday,
    )
    response = admin_client.post(
        f"/requests/{item.pk}/edit/",
        {**form_data, "created": yesterday.isoformat()},
    )
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.created == yesterday
    assert item.quantity == 3


def test_upload_material_photo(admin_client, form_data, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    material = Material.objects.get(pk=form_data["material"])
    url = f"/materials/{material.pk}/image/"
    bad_image = SimpleUploadedFile("invalid.png", b"invalid", "image/png")
    response = admin_client.post(url, {"image": bad_image})
    assert "image" in response.context["form"].errors
    material.refresh_from_db()
    assert not material.image
    for filename in ("paper.png", "replacement.png"):
        image = BytesIO()
        Image.new("RGB", (8, 8), "white").save(image, format="PNG")
        upload = SimpleUploadedFile(filename, image.getvalue(), "image/png")
        response = admin_client.post(url, {"image": upload}, follow=True)
        material.refresh_from_db()
        assert (tmp_path / material.image.name).is_file()
        assert filename in material.image.url
        assert material.image.url in response.content.decode()


def test_staff_without_permission_cannot_create(client, django_user_model,
                                                form_data):
    user = django_user_model.objects.create(username="viewer", is_staff=True)
    client.force_login(user)
    assert client.post("/requests/new/", form_data).status_code == 403
    assert not SupplyRequest.objects.exists()
