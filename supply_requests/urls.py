"""Маршруты заявок на снабжение."""

from django.urls import path

from . import views


app_name = "supply_requests"

urlpatterns = [
    path("", views.requests, name="requests"),
    path(
        "<int:request_id>/",
        views.request_detail,
        name="request_detail",
    ),
]
