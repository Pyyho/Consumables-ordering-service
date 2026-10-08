"""Конфигурация приложения заявок."""

from django.apps import AppConfig


class SupplyRequestsConfig(AppConfig):
    """Настроить приложение заявок на снабжение."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "supply_requests"
    verbose_name = "Заявки на снабжение"
