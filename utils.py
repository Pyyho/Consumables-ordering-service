"""Вспомогательные функции безопасного пользовательского ввода."""

from datetime import date, datetime
from typing import Optional


def input_int(prompt: str, minimum: Optional[int] = None) -> int:
    """Запрашивать целое число до получения корректного значения."""
    while True:
        try:
            value = int(input(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            suffix = f" не меньше {minimum}" if minimum is not None else ""
            print(f"Введите целое число{suffix}.")


def input_date(prompt: str) -> date:
    """Запрашивать дату в формате ДД.ММ.ГГГГ до корректного ввода."""
    while True:
        try:
            return datetime.strptime(input(prompt), "%d.%m.%Y").date()
        except ValueError:
            print("Введите дату в формате ДД.ММ.ГГГГ.")
