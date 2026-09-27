"""Преобразование JSON-данных в объекты проекта и обратно."""

import json
from pathlib import Path
from typing import Union

from models import Employee, Material, SupplyRequest
from models.materials import get_material
from models.users import get_employee


PathLike = Union[str, Path]


def load_json(filename: PathLike) -> list[dict]:
    """Загрузить список словарей; для отсутствующего файла вернуть []."""
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"файл {path} содержит некорректный JSON") from error

    if not isinstance(data, list):
        raise ValueError(f"в файле {path} ожидался список")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError(f"в файле {path} ожидался список объектов")
    return data


def save_json(filename: PathLike, data: list[dict]) -> None:
    """Сохранить список словарей через контекстный менеджер."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_materials(filename: PathLike) -> list[Material]:
    """Загрузить JSON и создать коллекцию объектов Material."""
    return [Material.from_data(data) for data in load_json(filename)]


def save_materials(filename: PathLike, materials: list[Material]) -> None:
    """Преобразовать материалы в словари и сохранить в JSON."""
    data = [
        {
            "id": material.id,
            "name": material.name,
            "unit": material.unit,
            "stock": material.stock,
        }
        for material in materials
    ]
    save_json(filename, data)


def load_employees(filename: PathLike) -> list[Employee]:
    """Загрузить JSON и создать коллекцию объектов Employee."""
    return [Employee.from_data(data) for data in load_json(filename)]


def save_employees(filename: PathLike, employees: list[Employee]) -> None:
    """Преобразовать сотрудников в словари и сохранить в JSON."""
    data = [
        {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
        }
        for employee in employees
    ]
    save_json(filename, data)


def load_requests(
    filename: PathLike,
    materials: list[Material],
    employees: list[Employee],
) -> list[SupplyRequest]:
    """Загрузить заявки и восстановить связи с объектами."""
    requests = []
    for data in load_json(filename):
        material_id = int(data["material_id"])
        employee_id = int(data["employee_id"])
        material = get_material(materials, material_id)
        employee = get_employee(employees, employee_id)
        if material is None:
            raise ValueError(
                f"для заявки №{data.get('id')} не найден материал "
                f"id={material_id}"
            )
        if employee is None:
            raise ValueError(
                f"для заявки №{data.get('id')} не найден сотрудник "
                f"id={employee_id}"
            )
        requests.append(SupplyRequest.from_data(data, employee, material))
    return requests


def save_requests(
    filename: PathLike, requests: list[SupplyRequest]
) -> None:
    """Заменить объектные ссылки идентификаторами и сохранить заявки."""
    data = [
        {
            "id": request.id,
            "employee_id": request.employee.id,
            "material_id": request.material.id,
            "quantity": request.quantity,
            "created": request.created.isoformat(),
            "status": request.status,
            "history": list(request.history),
        }
        for request in requests
    ]
    save_json(filename, data)
