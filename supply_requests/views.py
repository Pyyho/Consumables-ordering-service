"""ORM-представления ПР9: фильтры, поиск, сортировка и пагинация."""

from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from inventory.models import Material
from models.requests import FINAL_STATUSES
from staff.models import Employee

from .forms import RequestFilterForm, SORT_OPTIONS, SupplyRequestForm
from .models import RequestStatus, SupplyRequest


ACTIVE_STATUSES = [s for s in RequestStatus.values if s not in FINAL_STATUSES]


def _parse_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError
    return parsed


def _request_list(request, *, active_only=False):
    rows = SupplyRequest.objects.with_details()
    if active_only:
        rows = rows.active()
    form = RequestFilterForm(request.GET or None)
    invalid = form.is_bound and not form.is_valid()
    data = form.cleaned_data if form.is_bound else {}
    if invalid:
        rows = rows.none()
    else:
        for field, lookup in (
            ("date", "created"), ("material", "material"),
            ("employee", "employee"), ("status", "status"),
        ):
            if data.get(field):
                rows = rows.filter(**{lookup: data[field]})
        query = data.get("q")
        if query:
            rows = rows.filter(Q(material__name__icontains=query)
                               | Q(employee__name__icontains=query)
                               | Q(employee__department__icontains=query)
                               | Q(employee__email__icontains=query))
    sort_field = SORT_OPTIONS[data.get("sort") or "date"][0]
    page = Paginator(rows.order_by(sort_field, "pk"), 5).get_page(
        request.GET.get("page")
    )
    context = {
        "supply_requests": page, "page_obj": page,
        "active_only": active_only, "filter_form": form,
        "sort": data.get("sort") or "date",
        "error": " ".join(
            message for messages in form.errors.values()
            for message in messages
        ) if invalid else "",
    }
    return render(request, "supply_requests/request_list.html", context,
                  status=400 if invalid else 200)


def requests(request: HttpRequest) -> HttpResponse:
    return _request_list(request)


def active_requests(request: HttpRequest) -> HttpResponse:
    return _request_list(request, active_only=True)


def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    try:
        item = get_object_or_404(
            SupplyRequest.objects.with_details(),
            pk=request_id,
        )
    except Http404:
        return render(request, "supply_requests/request_detail.html",
                      {"supply_request": None, "history": []}, status=404)
    context = {"supply_request": item, "history": item.status_events.all()}
    return render(request, "supply_requests/request_detail.html", context)


def _request_form(request, item=None):
    editing = item is not None
    data = request.POST if request.method == "POST" else None
    form = SupplyRequestForm(data, instance=item)
    if request.method == "POST" and form.is_valid():
        try:
            item = form.save()
        except ValueError as error:
            form.add_error("quantity", str(error))
        else:
            return redirect("supply_requests:request_detail", item.pk)
    return render(request, "supply_requests/request_form.html",
                  {"form": form, "supply_request": item, "editing": editing})


@staff_member_required
@permission_required("supply_requests.add_supplyrequest", raise_exception=True)
@require_http_methods(["GET", "POST"])
def request_create(request):
    return _request_form(request)


@staff_member_required
@permission_required(
    "supply_requests.change_supplyrequest", raise_exception=True,
)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def request_edit(request, request_id):
    rows = SupplyRequest.objects
    if request.method == "POST":
        rows = rows.select_for_update()
    item = get_object_or_404(rows, pk=request_id)
    if not item.is_open:
        return render(request, "supply_requests/request_conflict.html",
                      {"supply_request": item}, status=409)
    return _request_form(request, item)


@require_POST
@staff_member_required
@permission_required(
    "supply_requests.change_supplyrequest", raise_exception=True,
)
def request_cancel(request, request_id):
    item = get_object_or_404(SupplyRequest, pk=request_id)
    try:
        item.cancel()
    except ValueError:
        return render(request, "supply_requests/request_conflict.html",
                      {"supply_request": item}, status=409)
    return redirect("supply_requests:request_detail", item.pk)


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
            context["supply_requests"] = (
                SupplyRequest.objects.with_details()
                .filter(created=parsed).order_by("pk")
            )
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
            completed=Count("pk", filter=Q(status=RequestStatus.COMPLETED))),
        "material_statistics": material_stats,
        "employee_statistics": employee_stats,
        "popular_materials": material_stats.filter(requests_count__gt=1),
        "departments": (
            Employee.objects.order_by().values("department")
            .annotate(requests_count=Count("supply_requests", filter=active))
            .filter(requests_count__gt=0)
            .order_by("-requests_count", "department")
        ),
        "recent_requests": SupplyRequest.objects.with_details().order_by(
            "-created", "-pk"
        )[:5],
        "without_active": Material.objects.exclude(
            pk__in=occupied_ids
        ).order_by("name", "pk"),
    }
    return render(request, "supply_requests/statistics.html", context)
