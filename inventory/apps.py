"""Конфигурация приложения каталога материалов."""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Настроить приложение каталога материалов."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
    verbose_name = "Материалы"
