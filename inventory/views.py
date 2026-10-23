"""Каталог и поиск материалов средствами параметризованных SQL-запросов."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all


def materials(request: HttpRequest) -> HttpResponse:
    """Получить список материалов из SQLite."""
    context = {"materials": fetch_all(
        "materials_list", db_path=settings.SUPPLY_DB_PATH
    )}
    return render(request, "inventory/material_list.html", context)


def material_detail(
    request: HttpRequest,
    material_id: int,
) -> HttpResponse:
    """Найти материал в SQLite и сохранить шаблонную обработку 404."""
    rows = fetch_all("material_detail", {"id": material_id},
                     db_path=settings.SUPPLY_DB_PATH)
    material = rows[0] if rows else None
    context = {
        "material": material,
        "available": material["stock"] > 0 if material is not None else False,
    }
    return render(
        request,
        "inventory/material_detail.html",
        context,
        status=404 if material is None else 200,
    )


def available_materials(request: HttpRequest) -> HttpResponse:
    """Найти материалы с остатком не меньше требуемого количества."""
    raw_quantity = request.GET.get("quantity", "")
    context = {"quantity": raw_quantity, "materials": [],
               "searched": bool(raw_quantity), "error": ""}
    if raw_quantity:
        try:
            quantity = int(raw_quantity)
            if not 1 <= quantity <= 2147483647:
                raise ValueError
        except ValueError:
            context["error"] = "Введите целое количество от 1 до 2147483647."
        else:
            context["materials"] = fetch_all(
                "materials_available", {"quantity": quantity},
                db_path=settings.SUPPLY_DB_PATH,
            )
    return render(request, "inventory/available.html", context,
                  status=400 if context["error"] else 200)
