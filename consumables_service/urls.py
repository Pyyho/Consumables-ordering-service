"""Маршруты верхнего уровня Django-проекта."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("materials/", include("inventory.urls")),
    path("requests/", include("supply_requests.urls")),
]
