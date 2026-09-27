"""Класс заявки и функции обработки коллекции заявок."""

from __future__ import annotations

from datetime import date
from typing import Optional, Union

from .materials import Material
from .users import Employee


VALID_STATUSES = (
    "Новая",
    "На согласовании",
    "Утверждена",
    "В закупке",
    "Выполнена",
    "Отклонена",
    "Отменена",
)

FINAL_STATUSES = {"Выполнена", "Отклонена", "Отменена"}


class SupplyRequest:
    """Заявка сотрудника на определённый расходный материал."""

    def __init__(
        self,
        request_id: int,
        employee: Employee,
        material: Material,
        quantity: int,
        created: Union[date, str],
        status: str = "Новая",
        history: Optional[list[str]] = None,
    ) -> None:
        """Создать заявку и связать сотрудника с материалом."""
        if request_id <= 0:
            raise ValueError("номер заявки должен быть положительным")
        if quantity <= 0:
            raise ValueError("количество должно быть больше нуля")
        if status not in VALID_STATUSES:
            raise ValueError(f"недопустимый статус '{status}'")

        self.id = request_id
        self.employee = employee
        self.material = material
        self.quantity = quantity
        self.created = self._parse_date(created)
        self._status = status
        self._history = list(history) if history else [status]
        if not self._history or self._history[-1] != status:
            self._history.append(status)

    @property
    def status(self) -> str:
        """Вернуть текущий статус заявки."""
        return self._status

    @property
    def history(self) -> tuple[str, ...]:
        """Вернуть неизменяемую копию истории статусов."""
        return tuple(self._history)

    @property
    def is_cancelled(self) -> bool:
        """Проверить, отменена ли заявка."""
        return self._status == "Отменена"

    @staticmethod
    def _parse_date(value: Union[date, str]) -> date:
        """Преобразовать ISO-строку в дату или вернуть переданную дату."""
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("дата должна иметь формат ГГГГ-ММ-ДД") from error

    @classmethod
    def from_data(
        cls,
        data: dict,
        employee: Employee,
        material: Material,
    ) -> SupplyRequest:
        """Восстановить заявку из JSON и связанных объектов."""
        history_data = data.get("history")
        history = (
            list(history_data) if isinstance(history_data, list) else None
        )
        return cls(
            request_id=int(data["id"]),
            employee=employee,
            material=material,
            quantity=int(data["quantity"]),
            created=str(data["created"]),
            status=str(data.get("status", "Новая")),
            history=history,
        )

    def change_status(self, new_status: str) -> None:
        """Изменить статус заявки и дополнить историю."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"недопустимый статус '{new_status}'")
        if self._status == new_status:
            return
        self._status = new_status
        self._history.append(new_status)

    def cancel(self) -> None:
        """Отменить заявку, если она не находится в конечном статусе."""
        if self._status in FINAL_STATUSES:
            raise ValueError("заявку в конечном статусе нельзя отменить")
        self.change_status("Отменена")

    def __str__(self) -> str:
        """Вернуть описание заявки со связанными объектами."""
        return (
            f"№{self.id} | {self.employee.name} | {self.material.name} — "
            f"{self.quantity} {self.material.unit} | "
            f"{self.created.isoformat()} | Статус: {self.status}"
        )


def get_request(
    requests: list[SupplyRequest], request_id: int
) -> Optional[SupplyRequest]:
    """Найти заявку по номеру."""
    return next(
        (request for request in requests if request.id == request_id),
        None,
    )


def create_request(
    requests: list[SupplyRequest],
    employee: Employee,
    material: Material,
    quantity: int,
    created: Optional[date] = None,
) -> SupplyRequest:
    """Создать связанную заявку, если материала достаточно на складе."""
    if not material.has_stock(quantity):
        raise ValueError("на складе недостаточно материала")
    request_id = max((request.id for request in requests), default=0) + 1
    request = SupplyRequest(
        request_id=request_id,
        employee=employee,
        material=material,
        quantity=quantity,
        created=created or date.today(),
    )
    requests.append(request)
    return request


def filter_requests(
    requests: list[SupplyRequest],
    status: Optional[str] = None,
    employee: Optional[str] = None,
    created: Optional[Union[date, str]] = None,
) -> list[SupplyRequest]:
    """Отобрать заявки по статусу, сотруднику и дате создания."""
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"недопустимый статус '{status}'")
    employee_query = employee.lower() if employee else None
    created_date = (
        SupplyRequest._parse_date(created) if created is not None else None
    )

    result = []
    for request in requests:
        if status is not None and request.status != status:
            continue
        if (
            employee_query
            and employee_query not in request.employee.name.lower()
        ):
            continue
        if created_date is not None and request.created != created_date:
            continue
        result.append(request)
    return result


def sort_requests(
    requests: list[SupplyRequest],
    by: str = "created",
    reverse: bool = False,
) -> list[SupplyRequest]:
    """Вернуть заявки, отсортированные по дате, статусу или номеру."""
    if by not in {"created", "status", "id"}:
        raise ValueError("неподдерживаемое поле сортировки")
    return sorted(
        requests,
        key=lambda request: getattr(request, by),
        reverse=reverse,
    )


def change_status(
    requests: list[SupplyRequest], request_id: int, new_status: str
) -> SupplyRequest:
    """Найти заявку и изменить её состояние методом объекта."""
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    request.change_status(new_status)
    return request


def cancel_request(
    requests: list[SupplyRequest], request_id: int
) -> SupplyRequest:
    """Найти заявку и вызвать её метод отмены."""
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    request.cancel()
    return request


def show_requests(requests: list[SupplyRequest]) -> str:
    """Сформировать текстовое представление коллекции заявок."""
    if not requests:
        return "Заявок не найдено"
    return "\n".join(str(request) for request in requests)


def show_history(
    requests: list[SupplyRequest], request_id: int
) -> str:
    """Сформировать строку истории изменения статусов заявки."""
    request = get_request(requests, request_id)
    if request is None:
        raise ValueError(f"заявка №{request_id} не найдена")
    return f"История заявки №{request_id}: " + " → ".join(request.history)
