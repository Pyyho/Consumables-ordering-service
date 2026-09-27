"""Классы пользователей и функции обработки сотрудников."""

from __future__ import annotations

from typing import Optional


class User:
    """Базовый пользователь системы."""

    def __init__(self, user_id: int, name: str, email: str) -> None:
        """Создать пользователя с общими атрибутами."""
        if user_id <= 0:
            raise ValueError(
                "идентификатор пользователя должен быть положительным"
            )
        if not name.strip():
            raise ValueError("имя пользователя не может быть пустым")
        if not self.validate_email(email):
            raise ValueError("некорректный адрес электронной почты")

        self.id = user_id
        self.name = name.strip()
        self.email = email.strip().lower()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Выполнить простую проверку адреса электронной почты."""
        local, separator, domain = email.strip().partition("@")
        return bool(local and separator and "." in domain)

    @classmethod
    def from_data(cls, data: dict) -> User:
        """Создать пользователя из данных JSON."""
        return cls(
            user_id=int(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
        )

    def __str__(self) -> str:
        """Вернуть строковое представление пользователя."""
        return f"id={self.id} | {self.name} | {self.email}"


class Employee(User):
    """Сотрудник организации, который создаёт заявки."""

    def __init__(
        self,
        employee_id: int,
        name: str,
        email: str,
        department: str,
    ) -> None:
        """Создать сотрудника и сохранить его подразделение."""
        super().__init__(employee_id, name, email)
        if not department.strip():
            raise ValueError("подразделение не может быть пустым")
        self.department = department.strip()

    @classmethod
    def from_data(cls, data: dict) -> Employee:
        """Создать сотрудника из данных JSON."""
        return cls(
            employee_id=int(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            department=str(data["department"]),
        )

    def __str__(self) -> str:
        """Вернуть специализированное представление сотрудника."""
        return (
            f"id={self.id} | {self.name} | {self.department} | "
            f"{self.email}"
        )


def get_employee(
    employees: list[Employee], employee_id: int
) -> Optional[Employee]:
    """Найти сотрудника по идентификатору."""
    return next(
        (
            employee
            for employee in employees
            if employee.id == employee_id
        ),
        None,
    )


def add_employee(
    employees: list[Employee],
    name: str,
    email: str,
    department: str,
) -> Employee:
    """Создать сотрудника и добавить его в коллекцию."""
    normalized_email = email.strip().lower()
    if any(employee.email == normalized_email for employee in employees):
        raise ValueError("сотрудник с такой электронной почтой уже существует")
    employee_id = max(
        (employee.id for employee in employees), default=0
    ) + 1
    employee = Employee(employee_id, name, email, department)
    employees.append(employee)
    return employee


def find_employee(
    employees: list[Employee], query: str
) -> list[Employee]:
    """Найти сотрудников по имени, почте или подразделению."""
    normalized_query = query.strip().lower()
    return [
        employee
        for employee in employees
        if normalized_query in employee.name.lower()
        or normalized_query in employee.email
        or normalized_query in employee.department.lower()
    ]


def show_employees(employees: list[User]) -> str:
    """Сформировать строки пользователей с полиморфным вызовом __str__."""
    if not employees:
        return "Сотрудники не найдены"
    return "\n".join(str(employee) for employee in employees)
