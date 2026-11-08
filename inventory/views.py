"""Каталог и подбор материалов средствами Django ORM."""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Material


def materials(request: HttpRequest) -> HttpResponse:
    context = {"materials": Material.objects.order_by("name", "pk")}
    return render(request, "inventory/material_list.html", context)


def material_detail(
    request: HttpRequest,
    material_id: int | None = None,
    slug: str | None = None,
) -> HttpResponse:
    try:
        lookup = {"slug": slug} if slug is not None else {"pk": material_id}
        material = get_object_or_404(Material, **lookup)
    except Http404:
        return render(request, "inventory/material_detail.html",
                      {"material": None}, status=404)
    context = {"material": material, "available": material.has_stock(1)}
    return render(request, "inventory/material_detail.html", context)


def available_materials(request: HttpRequest) -> HttpResponse:
    """Подбор по текущему остатку сохраняет правила ПР7, не вводит бронь."""
    raw_quantity = request.GET.get("quantity", "").strip()
    context = {"quantity": raw_quantity, "materials": Material.objects.none(),
               "searched": bool(raw_quantity), "error": ""}
    if raw_quantity:
        try:
            quantity = int(raw_quantity)
            if not 1 <= quantity <= 2147483647:
                raise ValueError
        except ValueError:
            context["error"] = "Введите целое количество от 1 до 2147483647."
        else:
            context["materials"] = Material.objects.filter(
                stock__gte=quantity
            ).order_by("stock", "name", "pk")
    return render(request, "inventory/available.html", context,
                  status=400 if context["error"] else 200)
