"""Функции для оформления и обработки заявок на материалы."""

from datetime import date
from typing import Optional

from materials import check_stock, get_material


VALID_STATUSES = (
    "Новая",
    "На согласовании",
    "Утверждена",
    "В закупке",
    "Выполнена",
    "Отклонена",
    "Отменена",
)


def get_request(
    requests: list[dict], request_id: int
) -> Optional[dict]:
    """Найти заявку по номеру."""
    return next(
        (
            request
            for request in requests
            if request["id"] == request_id
        ),
        None,
    )


def create_request(
    requests: list[dict],
    materials: list[dict],
    employee: str,
    material_id: int,
    quantity: int,
    created: Optional[date] = None,
) -> dict:
    """Создать заявку, если материал существует и есть на складе."""
    if not employee.strip():
        raise ValueError("имя сотрудника не может быть пустым")
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    if not check_stock(materials, material_id, quantity):
        raise ValueError("на складе недостаточно материала")

    request_id = max(
        (request["id"] for request in requests), default=0
    ) + 1
    request = {
        "id": request_id,
        "employee": employee.strip(),
        "material_id": material_id,
        "quantity": quantity,
        "created": (created or date.today()).isoformat(),
        "status": "Новая",
        "history": ["Новая"],
    }
    requests.append(request)
    return request


def filter_requests(
    requests: list[dict],
    status: Optional[str] = None,
    employee: Optional[str] = None,
    created: Optional[str] = None,
) -> list[dict]:
    """Отобрать заявки по статусу, сотруднику и дате создания."""
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"недопустимый статус '{status}'")

    employee_query = employee.lower() if employee else None
    result = []
    for request in requests:
        if status is not None and request["status"] != status:
            continue
        if employee_query and employee_query not in str(
            request["employee"]
        ).lower():
            continue
        if created is not None and request["created"] != created:
            continue
        result.append(request)
    return result


def sort_requests(
    requests: list[dict], by: str = "created", reverse: bool = False
) -> list[dict]:
    """Вернуть заявки, отсортированные по дате, статусу или номеру."""
    if by not in {"created", "status", "id"}:
        raise ValueError("неподдерживаемое поле сортировки")
    return sorted(
        requests,
        key=lambda request: request[by],
        reverse=reverse,
    )


def change_status(
    requests: list[dict], request_id: int, new_status: str
) -> dict:
    """Изменить статус заявки и дополнить историю статусов."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"недопустимый статус '{new_status}'")
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    if request["status"] == new_status:
        return request
    request["status"] = new_status
    request["history"].append(new_status)
    return request


def cancel_request(requests: list[dict], request_id: int) -> dict:
    """Отменить заявку, если она ещё не выполнена или отклонена."""
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    if request["status"] in {"Выполнена", "Отклонена", "Отменена"}:
        raise ValueError("заявку в конечном статусе нельзя отменить")
    return change_status(requests, request_id, "Отменена")


def show_requests(requests: list[dict]) -> str:
    """Сформировать текстовое представление списка заявок."""
    if not requests:
        return "Заявок не найдено"
    lines = []
    for request in requests:
        lines.append(
            f"№{request['id']} | {request['employee']} | "
            f"материал id={request['material_id']} — "
            f"{request['quantity']} | {request['created']} | "
            f"Статус: {request['status']}"
        )
    return "\n".join(lines)


def show_history(requests: list[dict], request_id: int) -> str:
    """Сформировать строку истории изменения статусов заявки."""
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    return (
        f"История заявки №{request_id}: "
        + " → ".join(request["history"])
    )
