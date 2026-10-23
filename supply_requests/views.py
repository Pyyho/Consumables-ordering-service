"""Заявки, сотрудники и статистика на основе запросов sqlite3."""

from datetime import date

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all


def requests(request: HttpRequest) -> HttpResponse:
    """Показать все заявки с сотрудниками и материалами через JOIN."""
    context = {"supply_requests": fetch_all(
        "requests_all", db_path=settings.SUPPLY_DB_PATH
    )}
    return render(request, "supply_requests/request_list.html", context)


def request_detail(
    request: HttpRequest,
    request_id: int,
) -> HttpResponse:
    """Получить связанные данные и историю заявки из SQLite."""
    rows = fetch_all("request_detail", {"id": request_id},
                     db_path=settings.SUPPLY_DB_PATH)
    supply_request = rows[0] if rows else None
    history = fetch_all("request_history", {"id": request_id},
                        db_path=settings.SUPPLY_DB_PATH)
    context = {"supply_request": supply_request, "history": history}
    return render(
        request,
        "supply_requests/request_detail.html",
        context,
        status=404 if supply_request is None else 200,
    )


def active_requests(request: HttpRequest) -> HttpResponse:
    """Показать заявки, которые ещё обрабатываются."""
    context = {
        "supply_requests": fetch_all("requests_active",
                                     db_path=settings.SUPPLY_DB_PATH),
        "active_only": True,
    }
    return render(request, "supply_requests/request_list.html", context)


def requests_by_date(request: HttpRequest) -> HttpResponse:
    """Выполнить поиск заявок по проверенной ISO-дате создания."""
    selected_date = request.GET.get("date", "")
    context = {"selected_date": selected_date, "supply_requests": [],
               "searched": bool(selected_date), "error": ""}
    if selected_date:
        try:
            if date.fromisoformat(selected_date).isoformat() != selected_date:
                raise ValueError
        except ValueError:
            context["error"] = "Введите дату в формате ГГГГ-ММ-ДД."
        else:
            context["supply_requests"] = fetch_all(
                "requests_on_date", {"created": selected_date},
                db_path=settings.SUPPLY_DB_PATH,
            )
    return render(request, "supply_requests/search.html", context,
                  status=400 if context["error"] else 200)


def employees(request: HttpRequest) -> HttpResponse:
    """Показать справочник сотрудников, импортированный из JSON."""
    context = {"employees": fetch_all("employees_list",
                                      db_path=settings.SUPPLY_DB_PATH)}
    return render(request, "supply_requests/employees.html", context)


def statistics(request: HttpRequest) -> HttpResponse:
    """Показать агрегаты и группировки для анализа снабжения."""
    db_path = settings.SUPPLY_DB_PATH
    context = {
        "material_summary": fetch_all("material_summary", db_path=db_path)[0],
        "request_summary": fetch_all("request_summary", db_path=db_path)[0],
        "material_statistics": fetch_all(
            "material_statistics", db_path=db_path
        ),
        "employee_statistics": fetch_all(
            "employee_statistics", db_path=db_path
        ),
        "popular_materials": fetch_all("popular_materials", {"minimum": 1},
                                       db_path=db_path),
        "departments": fetch_all("department_statistics", {"minimum": 0},
                                 db_path=db_path),
        "recent_requests": fetch_all(
            "recent_requests", {"limit": 5, "offset": 0}, db_path=db_path
        ),
        "without_active": fetch_all(
            "materials_without_active", db_path=db_path
        ),
    }
    return render(request, "supply_requests/statistics.html", context)
