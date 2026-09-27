"""Совместимый импорт классов и функций сотрудников ПР3."""

from models.users import (
    Employee,
    User,
    add_employee,
    find_employee,
    get_employee,
    show_employees,
)

__all__ = [
    "Employee",
    "User",
    "add_employee",
    "find_employee",
    "get_employee",
    "show_employees",
]
