"""Класс материала и функции обработки коллекции материалов."""

from __future__ import annotations

from typing import Optional


class Material:
    """Расходный материал, доступный для заказа сотрудниками."""

    def __init__(
        self,
        material_id: int,
        name: str,
        unit: str,
        stock: int,
    ) -> None:
        """Создать материал и проверить корректность его данных."""
        if material_id <= 0:
            raise ValueError(
                "идентификатор материала должен быть положительным"
            )
        if not name.strip():
            raise ValueError("название материала не может быть пустым")
        if not unit.strip():
            raise ValueError("единица измерения не может быть пустой")
        if not self.validate_stock(stock):
            raise ValueError("остаток не может быть отрицательным")

        self.id = material_id
        self.name = name.strip()
        self.unit = unit.strip()
        self._stock = stock

    @property
    def stock(self) -> int:
        """Вернуть текущий остаток материала."""
        return self._stock

    @staticmethod
    def validate_stock(stock: int) -> bool:
        """Проверить, что остаток является неотрицательным числом."""
        return isinstance(stock, int) and stock >= 0

    @classmethod
    def from_data(cls, data: dict) -> Material:
        """Создать объект материала из данных JSON."""
        return cls(
            material_id=int(data["id"]),
            name=str(data["name"]),
            unit=str(data["unit"]),
            stock=int(data["stock"]),
        )

    def has_stock(self, quantity: int) -> bool:
        """Проверить наличие требуемого количества на складе."""
        if quantity <= 0:
            raise ValueError("количество должно быть больше нуля")
        return self._stock >= quantity

    def update(
        self,
        name: Optional[str] = None,
        unit: Optional[str] = None,
        stock: Optional[int] = None,
    ) -> None:
        """Изменить переданные характеристики материала."""
        if name is not None:
            if not name.strip():
                raise ValueError("название материала не может быть пустым")
            self.name = name.strip()
        if unit is not None:
            if not unit.strip():
                raise ValueError("единица измерения не может быть пустой")
            self.unit = unit.strip()
        if stock is not None:
            if not self.validate_stock(stock):
                raise ValueError("остаток не может быть отрицательным")
            self._stock = stock

    def __str__(self) -> str:
        """Вернуть удобное строковое представление материала."""
        return (
            f"id={self.id} | {self.name} ({self.unit}) | "
            f"Остаток: {self.stock}"
        )


def get_material(
    materials: list[Material], material_id: int
) -> Optional[Material]:
    """Найти материал по идентификатору."""
    return next(
        (material for material in materials if material.id == material_id),
        None,
    )


def add_material(
    materials: list[Material], name: str, unit: str, stock: int
) -> Material:
    """Создать материал, добавить его в коллекцию и вернуть объект."""
    material_id = max(
        (material.id for material in materials), default=0
    ) + 1
    material = Material(material_id, name, unit, stock)
    materials.append(material)
    return material


def update_material(
    materials: list[Material],
    material_id: int,
    name: Optional[str] = None,
    unit: Optional[str] = None,
    stock: Optional[int] = None,
) -> Material:
    """Найти материал и изменить переданные характеристики."""
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    material.update(name=name, unit=unit, stock=stock)
    return material


def delete_material(
    materials: list[Material], material_id: int
) -> Material:
    """Удалить материал из коллекции и вернуть удалённый объект."""
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    materials.remove(material)
    return material


def find_material(
    materials: list[Material], query: str
) -> list[Material]:
    """Найти материалы по части названия без учёта регистра."""
    normalized_query = query.strip().lower()
    return [
        material
        for material in materials
        if normalized_query in material.name.lower()
    ]


def check_stock(
    materials: list[Material], material_id: int, quantity: int
) -> bool:
    """Найти материал и проверить его остаток методом объекта."""
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    return material.has_stock(quantity)


def filter_materials_by_stock(
    materials: list[Material], minimum: int
) -> list[Material]:
    """Вернуть материалы с остатком не меньше заданного."""
    if minimum < 0:
        raise ValueError("минимальный остаток не может быть отрицательным")
    return [material for material in materials if material.stock >= minimum]


def sort_materials(
    materials: list[Material],
    by: str = "name",
    reverse: bool = False,
) -> list[Material]:
    """Вернуть новый список материалов, отсортированный по полю."""
    if by not in {"name", "stock"}:
        raise ValueError("сортировка доступна только по name или stock")
    return sorted(
        materials,
        key=lambda material: getattr(material, by),
        reverse=reverse,
    )


def show_materials(materials: list[Material]) -> str:
    """Сформировать текстовое представление коллекции материалов."""
    if not materials:
        return "Материалы не найдены"
    return "\n".join(str(material) for material in materials)
