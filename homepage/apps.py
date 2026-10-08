"""Конфигурация приложения главной страницы."""

from django.apps import AppConfig


class HomepageConfig(AppConfig):
    """Настроить приложение главной страницы."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "homepage"
    verbose_name = "Главная страница"
