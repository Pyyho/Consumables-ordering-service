"""Представления каталога расходных материалов на Django-шаблонах."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.materials import get_material
from storage import load_materials


def materials(request: HttpRequest) -> HttpResponse:
    """Загрузить объекты материалов и передать коллекцию в шаблон."""
    materials_file = settings.BASE_DIR / "data" / "materials.json"
    context = {"materials": load_materials(materials_file)}
    return render(request, "inventory/material_list.html", context)


def material_detail(
    request: HttpRequest,
    material_id: int,
) -> HttpResponse:
    """Передать материал или None в шаблон с правильным HTTP-статусом."""
    materials_file = settings.BASE_DIR / "data" / "materials.json"
    material = get_material(load_materials(materials_file), material_id)
    context = {
        "material": material,
        "available": material.has_stock(1) if material is not None else False,
    }
    return render(
        request,
        "inventory/material_detail.html",
        context,
        status=404 if material is None else 200,
    )
