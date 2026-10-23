"""Выполнить все учебные запросы и показать результаты в терминале."""

from db.queries import fetch_all, load_queries


SAMPLE_PARAMS = {
    "materials_available": {"quantity": 5},
    "material_detail": {"id": 1},
    "requests_on_date": {"created": "2026-09-20"},
    "request_detail": {"id": 1},
    "request_history": {"id": 1},
    "popular_materials": {"minimum": 1},
    "department_statistics": {"minimum": 0},
    "recent_requests": {"limit": 5, "offset": 0},
}


if __name__ == "__main__":
    for name in load_queries():
        rows = fetch_all(name, SAMPLE_PARAMS.get(name))
        print(name, [dict(row) for row in rows])
