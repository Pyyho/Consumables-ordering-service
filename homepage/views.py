"""Общий HTML-каркас и главная страница сервиса."""

from html import escape

from django.http import HttpRequest, HttpResponse


BOOTSTRAP_URL = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
    "dist/css/bootstrap.min.css"
)


def page(title: str, content: str) -> str:
    """Сформировать единый HTML-документ с навигацией."""
    safe_title = escape(title)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe_title}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_URL}">
    <style>
        body {{ background: #f5f7fa; }}
        .service-header {{ background: #17324d; }}
        .summary-card {{ border: 0; box-shadow: 0 0.4rem 1.2rem #1f293714; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark service-header mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Расходные материалы</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Главная</a>
                <a class="nav-link" href="/materials/">Материалы</a>
                <a class="nav-link" href="/requests/">Заявки</a>
            </div>
        </div>
    </nav>
    <main class="container pb-5">{content}</main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    """Показать назначение сервиса и ссылки на основные разделы."""
    content = """
<section class="p-5 bg-white rounded-3 summary-card">
    <h1 class="display-5 fw-semibold">Сервис заказа расходных материалов</h1>
    <p class="lead mb-4">
        Веб-интерфейс для просмотра складских остатков и заявок сотрудников.
    </p>
    <a href="/materials/" class="btn btn-primary me-2">
        Каталог материалов
    </a>
    <a href="/requests/" class="btn btn-outline-primary">
        Заявки на снабжение
    </a>
</section>
"""
    return HttpResponse(page("Сервис расходных материалов", content))
