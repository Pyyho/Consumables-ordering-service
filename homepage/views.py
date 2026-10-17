"""Главная страница сервиса заказа расходных материалов."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Показать описание сервиса и навигацию через базовый шаблон."""
    return render(request, "homepage/index.html")
