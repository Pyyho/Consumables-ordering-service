"""Представления заявок сотрудников на Django-шаблонах."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.requests import SupplyRequest, get_request
from storage import load_employees, load_materials, load_requests


def _load_requests() -> list[SupplyRequest]:
    """Загрузить заявки и восстановить связи с сотрудниками и материалами."""
    data_dir = settings.BASE_DIR / "data"
    materials = load_materials(data_dir / "materials.json")
    employees = load_employees(data_dir / "employees.json")
    return load_requests(data_dir / "requests.json", materials, employees)


def requests(request: HttpRequest) -> HttpResponse:
    """Передать список заявок в шаблон с циклом и включаемым статусом."""
    context = {"supply_requests": _load_requests()}
    return render(request, "supply_requests/request_list.html", context)


def request_detail(
    request: HttpRequest,
    request_id: int,
) -> HttpResponse:
    """Показать заявку или шаблонное сообщение с HTTP-статусом 404."""
    supply_request = get_request(_load_requests(), request_id)
    context = {"supply_request": supply_request}
    return render(
        request,
        "supply_requests/request_detail.html",
        context,
        status=404 if supply_request is None else 200,
    )
