"""Маршруты каталога материалов."""

from django.urls import path

from . import views


app_name = "inventory"

urlpatterns = [
    path("", views.materials, name="materials"),
    path("available/", views.available_materials, name="available"),
    path(
        "<int:material_id>/",
        views.material_detail,
        name="material_detail",
    ),
    path("<int:material_id>/image/", views.material_image, name="image"),
    path("<slug:slug>/", views.material_detail, name="material_by_slug"),
]
