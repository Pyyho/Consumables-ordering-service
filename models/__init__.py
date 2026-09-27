"""Объектная модель сервиса заказа расходных материалов."""

from .materials import Material
from .requests import SupplyRequest
from .users import Employee, User

__all__ = ["Employee", "Material", "SupplyRequest", "User"]
