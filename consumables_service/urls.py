"""Маршруты верхнего уровня Django-проекта."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Управление снабжением"
admin.site.site_title = "Снабжение"
admin.site.index_title = "Материалы, сотрудники и заявки"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("materials/", include("inventory.urls")),
    path("requests/", include("supply_requests.urls")),
]

if settings.ENABLE_DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
