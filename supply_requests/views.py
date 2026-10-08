"""Страницы заявок сотрудников на расходные материалы."""

from html import escape

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from homepage.views import page
from models.requests import SupplyRequest, get_request
from storage import load_employees, load_materials, load_requests


DATA_DIR = settings.BASE_DIR / "data"

STATUS_BADGES = {
    "Новая": "text-bg-primary",
    "На согласовании": "text-bg-warning",
    "Утверждена": "text-bg-info",
    "В закупке": "text-bg-dark",
    "Выполнена": "text-bg-success",
    "Отклонена": "text-bg-danger",
    "Отменена": "text-bg-secondary",
}


def _load_requests() -> list[SupplyRequest]:
    """Загрузить заявки и восстановить ссылки на связанные объекты."""
    materials = load_materials(DATA_DIR / "materials.json")
    employees = load_employees(DATA_DIR / "employees.json")
    return load_requests(
        DATA_DIR / "requests.json",
        materials,
        employees,
    )


def requests(request: HttpRequest) -> HttpResponse:
    """Показать все заявки из JSON-хранилища ПР3."""
    request_items = _load_requests()
    rows = []
    for item in request_items:
        badge = STATUS_BADGES.get(item.status, "text-bg-secondary")
        rows.append(
            f"""
<tr>
    <td>
        <a href="/requests/{item.id}/" class="fw-semibold">
            №{item.id}
        </a>
    </td>
    <td>{escape(item.employee.name)}</td>
    <td>{escape(item.material.name)}</td>
    <td>{item.quantity} {escape(item.material.unit)}</td>
    <td>{item.created.strftime('%d.%m.%Y')}</td>
    <td><span class="badge {badge}">{escape(item.status)}</span></td>
</tr>
"""
        )

    content = f"""
<div class="d-flex justify-content-between align-items-center mb-3">
    <div>
        <h1 class="mb-1">Заявки на снабжение</h1>
        <p class="text-body-secondary mb-0">
            Заявки сотрудников из data/requests.json
        </p>
    </div>
    <span class="badge text-bg-primary">Заявок: {len(request_items)}</span>
</div>
<div class="table-responsive bg-white rounded summary-card">
    <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
            <tr>
                <th>Номер</th>
                <th>Сотрудник</th>
                <th>Материал</th>
                <th>Количество</th>
                <th>Дата</th>
                <th>Статус</th>
            </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
"""
    return HttpResponse(page("Заявки на снабжение", content))


def request_detail(
    request: HttpRequest,
    request_id: int,
) -> HttpResponse:
    """Показать заявку или вернуть страницу с кодом 404."""
    supply_request = get_request(_load_requests(), request_id)
    if supply_request is None:
        content = """
<div class="alert alert-danger" role="alert">
    <h1 class="h3">Заявка не найдена</h1>
    <p>Заявки с таким номером нет в хранилище.</p>
</div>
<a href="/requests/" class="btn btn-outline-secondary">
    К списку заявок
</a>
"""
        return HttpResponse(
            page("Заявка не найдена", content),
            status=404,
        )

    badge = STATUS_BADGES.get(
        supply_request.status,
        "text-bg-secondary",
    )
    history = "".join(
        f'<li class="list-group-item">{escape(status)}</li>'
        for status in supply_request.history
    )
    content = f"""
<div class="card summary-card">
    <div class="card-body p-4">
        <div class="d-flex justify-content-between align-items-start">
            <h1 class="card-title h2">Заявка №{supply_request.id}</h1>
            <span class="badge {badge}">
                {escape(supply_request.status)}
            </span>
        </div>
        <dl class="row mt-4">
            <dt class="col-sm-4">Сотрудник</dt>
            <dd class="col-sm-8">{escape(supply_request.employee.name)}</dd>
            <dt class="col-sm-4">Подразделение</dt>
            <dd class="col-sm-8">
                {escape(supply_request.employee.department)}
            </dd>
            <dt class="col-sm-4">Материал</dt>
            <dd class="col-sm-8">
                <a href="/materials/{supply_request.material.id}/">
                    {escape(supply_request.material.name)}
                </a>
            </dd>
            <dt class="col-sm-4">Количество</dt>
            <dd class="col-sm-8">
                {supply_request.quantity}
                {escape(supply_request.material.unit)}
            </dd>
            <dt class="col-sm-4">Дата создания</dt>
            <dd class="col-sm-8">
                {supply_request.created.strftime('%d.%m.%Y')}
            </dd>
        </dl>
        <h2 class="h5 mt-4">История статусов</h2>
        <ul class="list-group list-group-flush mb-4">{history}</ul>
        <a href="/requests/" class="btn btn-outline-secondary">
            К списку заявок
        </a>
    </div>
</div>
"""
    return HttpResponse(
        page(f"Заявка №{supply_request.id}", content)
    )
