"""ORM-представления ПР9: фильтры, поиск, сортировка и пагинация."""

from datetime import date

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from inventory.models import Material
from models.requests import FINAL_STATUSES, VALID_STATUSES
from staff.models import Employee

from .models import SupplyRequest


ACTIVE_STATUSES = [s for s in VALID_STATUSES if s not in FINAL_STATUSES]
SORT_FIELDS = {"date": "created", "newest": "-created",
               "material": "material__name", "employee": "employee__name",
               "status": "status"}


def _parse_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError
    return parsed


def _request_list(request, *, active_only=False):
    rows = SupplyRequest.objects.select_related("material", "employee")
    if active_only:
        rows = rows.active()
    selected_date = request.GET.get("date", "").strip()
    selected_material = request.GET.get("material", "").strip()
    selected_employee = request.GET.get("employee", "").strip()
    selected_status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "date")
    if sort not in SORT_FIELDS:
        sort = "date"
    errors = []
    if selected_date:
        try:
            rows = rows.filter(created=_parse_date(selected_date))
        except ValueError:
            errors.append("Введите дату в формате ГГГГ-ММ-ДД.")
    for name, raw in (("material_id", selected_material),
                      ("employee_id", selected_employee)):
        if raw:
            try:
                value = int(raw)
                if not 1 <= value <= 2147483647:
                    raise ValueError
            except ValueError:
                errors.append("Выберите корректный материал и сотрудника.")
            else:
                rows = rows.filter(**{name: value})
    if selected_status:
        if selected_status not in VALID_STATUSES:
            errors.append("Выберите допустимый статус.")
        else:
            rows = rows.filter(status=selected_status)
    if query:
        rows = rows.filter(Q(material__name__icontains=query)
                           | Q(employee__name__icontains=query)
                           | Q(employee__department__icontains=query)
                           | Q(employee__email__icontains=query))
    if errors:
        rows = rows.none()
    rows = rows.order_by(SORT_FIELDS[sort], "pk")
    page = Paginator(rows, 5).get_page(request.GET.get("page"))
    context = {
        "supply_requests": page, "page_obj": page,
        "active_only": active_only, "selected_date": selected_date,
        "selected_material": selected_material,
        "selected_employee": selected_employee,
        "selected_status": selected_status, "q": query, "sort": sort,
        "materials": Material.objects.order_by("name", "pk"),
        "employees": Employee.objects.order_by("name", "pk"),
        "statuses": VALID_STATUSES, "error": " ".join(errors),
    }
    return render(request, "supply_requests/request_list.html", context,
                  status=400 if errors else 200)


def requests(request: HttpRequest) -> HttpResponse:
    return _request_list(request)


def active_requests(request: HttpRequest) -> HttpResponse:
    return _request_list(request, active_only=True)


def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    try:
        item = get_object_or_404(
            SupplyRequest.objects.select_related("material", "employee"),
            pk=request_id,
        )
    except Http404:
        return render(request, "supply_requests/request_detail.html",
                      {"supply_request": None, "history": []}, status=404)
    context = {"supply_request": item, "history": item.status_events.all()}
    return render(request, "supply_requests/request_detail.html", context)


def requests_by_date(request: HttpRequest) -> HttpResponse:
    selected_date = request.GET.get("date", "").strip()
    context = {"selected_date": selected_date,
               "supply_requests": SupplyRequest.objects.none(),
               "searched": bool(selected_date), "error": ""}
    if selected_date:
        try:
            parsed = _parse_date(selected_date)
        except ValueError:
            context["error"] = "Введите дату в формате ГГГГ-ММ-ДД."
        else:
            context["supply_requests"] = SupplyRequest.objects.filter(
                created=parsed
            ).select_related("material", "employee").order_by("pk")
    return render(request, "supply_requests/search.html", context,
                  status=400 if context["error"] else 200)


def employees(request: HttpRequest) -> HttpResponse:
    context = {"employees": Employee.objects.order_by(
        "department", "name", "pk"
    )}
    return render(request, "supply_requests/employees.html", context)


def statistics(request: HttpRequest) -> HttpResponse:
    active = Q(supply_requests__status__in=ACTIVE_STATUSES)
    material_stats = Material.objects.annotate(
        requests_count=Count("supply_requests", filter=active),
        requested_quantity=Coalesce(Sum("supply_requests__quantity",
                                        filter=active), 0),
        average_quantity=Avg("supply_requests__quantity", filter=active),
        minimum_quantity=Min("supply_requests__quantity", filter=active),
        maximum_quantity=Max("supply_requests__quantity", filter=active),
    ).order_by("-requests_count", "pk")
    employee_stats = Employee.objects.annotate(
        requests_count=Count("supply_requests", filter=active)
    ).order_by("-requests_count", "pk")
    occupied_ids = SupplyRequest.objects.active().values_list(
        "material_id", flat=True
    )
    context = {
        "material_summary": Material.objects.aggregate(
            total=Count("pk"), in_stock=Count("pk", filter=Q(stock__gt=0))),
        "request_summary": SupplyRequest.objects.aggregate(
            total=Count("pk"),
            active=Count("pk", filter=Q(status__in=ACTIVE_STATUSES)),
            completed=Count("pk", filter=Q(status="Выполнена"))),
        "material_statistics": material_stats,
        "employee_statistics": employee_stats,
        "popular_materials": material_stats.filter(requests_count__gt=1),
        "departments": (
            Employee.objects.order_by().values("department")
            .annotate(requests_count=Count("supply_requests", filter=active))
            .filter(requests_count__gt=0)
            .order_by("-requests_count", "department")
        ),
        "recent_requests": SupplyRequest.objects.select_related(
            "employee", "material"
        ).order_by("-created", "-pk")[:5],
        "without_active": Material.objects.exclude(
            pk__in=occupied_ids
        ).order_by("name", "pk"),
    }
    return render(request, "supply_requests/statistics.html", context)
