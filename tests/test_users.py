"""Тесты классов User и Employee."""

import pytest

from models import Employee, User
from models.users import add_employee, find_employee, show_employees


def test_user_creation() -> None:
    user = User(1, "Иванов И.И.", "ivanov@example.local")
    assert user.id == 1
    assert user.name == "Иванов И.И."
    assert "ivanov@example.local" in str(user)


def test_employee_inherits_user_and_overrides_string() -> None:
    employee = Employee(
        1,
        "Иванов И.И.",
        "ivanov@example.local",
        "Снабжение",
    )
    assert isinstance(employee, User)
    assert employee.department == "Снабжение"
    assert "Снабжение" in str(employee)


def test_employee_from_data() -> None:
    employee = Employee.from_data(
        {
            "id": 1,
            "name": "Иванов И.И.",
            "email": "ivanov@example.local",
            "department": "Снабжение",
        }
    )
    assert isinstance(employee, Employee)
    assert employee.id == 1


def test_add_and_find_employee() -> None:
    employees = []
    employee = add_employee(
        employees,
        "Петрова А.С.",
        "petrova@example.local",
        "Бухгалтерия",
    )
    assert employee.id == 1
    assert find_employee(employees, "бухгалтерия") == [employee]


def test_duplicate_email_is_rejected() -> None:
    employees = [
        Employee(1, "Иванов", "ivanov@example.local", "Снабжение")
    ]
    with pytest.raises(ValueError, match="уже существует"):
        add_employee(
            employees,
            "Иванов И.И.",
            "IVANOV@example.local",
            "Склад",
        )


def test_polymorphic_user_output() -> None:
    users: list[User] = [
        User(1, "Администратор", "admin@example.local"),
        Employee(2, "Иванов", "ivanov@example.local", "Снабжение"),
    ]
    output = show_employees(users)
    assert "Администратор" in output
    assert "Снабжение" in output
