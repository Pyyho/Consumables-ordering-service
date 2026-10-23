"""Маршруты заявок на снабжение."""

from django.urls import path

from . import views


app_name = "supply_requests"

urlpatterns = [
    path("", views.requests, name="requests"),
    path("active/", views.active_requests, name="active"),
    path("search/", views.requests_by_date, name="search"),
    path("employees/", views.employees, name="employees"),
    path("statistics/", views.statistics, name="statistics"),
    path(
        "<int:request_id>/",
        views.request_detail,
        name="request_detail",
    ),
]
