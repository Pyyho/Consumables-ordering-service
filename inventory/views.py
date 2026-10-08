"""Страницы каталога расходных материалов."""

from html import escape

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from homepage.views import page
from models.materials import get_material
from storage import load_materials


MATERIALS_FILE = settings.BASE_DIR / "data" / "materials.json"


def materials(request: HttpRequest) -> HttpResponse:
    """Показать материалы, загруженные из JSON-хранилища ПР3."""
    items = []
    for material in load_materials(MATERIALS_FILE):
        badge = "bg-success" if material.has_stock(1) else "bg-danger"
        stock_text = f"{material.stock} {escape(material.unit)}"
        items.append(
            f"""
<a href="/materials/{material.id}/"
   class="list-group-item list-group-item-action d-flex
          justify-content-between align-items-center">
    <span>
        <strong>{escape(material.name)}</strong>
        <small class="text-body-secondary ms-2">ID {material.id}</small>
    </span>
    <span class="badge {badge} rounded-pill">{stock_text}</span>
</a>
"""
        )

    content = f"""
<div class="d-flex justify-content-between align-items-center mb-3">
    <div>
        <h1 class="mb-1">Расходные материалы</h1>
        <p class="text-body-secondary mb-0">
            Актуальные остатки из data/materials.json
        </p>
    </div>
    <span class="badge text-bg-primary">Позиций: {len(items)}</span>
</div>
<div class="list-group summary-card">{''.join(items)}</div>
"""
    return HttpResponse(page("Расходные материалы", content))


def material_detail(
    request: HttpRequest,
    material_id: int,
) -> HttpResponse:
    """Показать материал или вернуть страницу с кодом 404."""
    material = get_material(load_materials(MATERIALS_FILE), material_id)
    if material is None:
        content = """
<div class="alert alert-danger" role="alert">
    <h1 class="h3">Материал не найден</h1>
    <p>Позиции с таким идентификатором нет в справочнике.</p>
</div>
<a href="/materials/" class="btn btn-outline-secondary">
    К списку материалов
</a>
"""
        return HttpResponse(
            page("Материал не найден", content),
            status=404,
        )

    available = material.has_stock(1)
    status_text = "В наличии" if available else "Нет на складе"
    badge = "text-bg-success" if available else "text-bg-danger"
    content = f"""
<div class="card summary-card">
    <div class="card-body p-4">
        <div class="d-flex justify-content-between align-items-start">
            <h1 class="card-title h2">{escape(material.name)}</h1>
            <span class="badge {badge}">{status_text}</span>
        </div>
        <dl class="row mt-4 mb-4">
            <dt class="col-sm-4">Идентификатор</dt>
            <dd class="col-sm-8">{material.id}</dd>
            <dt class="col-sm-4">Единица измерения</dt>
            <dd class="col-sm-8">{escape(material.unit)}</dd>
            <dt class="col-sm-4">Остаток</dt>
            <dd class="col-sm-8">{material.stock}</dd>
        </dl>
        <a href="/materials/" class="btn btn-outline-secondary">
            К списку материалов
        </a>
    </div>
</div>
"""
    return HttpResponse(page(material.name, content))
