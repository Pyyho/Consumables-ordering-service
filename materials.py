"""Функции для работы со справочником расходных материалов."""

from typing import Optional


def get_material(
    materials: list[dict], material_id: int
) -> Optional[dict]:
    """Найти материал по идентификатору."""
    return next(
        (
            material
            for material in materials
            if material["id"] == material_id
        ),
        None,
    )


def add_material(
    materials: list[dict], name: str, unit: str, stock: int
) -> dict:
    """Добавить материал в справочник и вернуть созданную запись."""
    if not name.strip():
        raise ValueError("название материала не может быть пустым")
    if not unit.strip():
        raise ValueError("единица измерения не может быть пустой")
    if stock < 0:
        raise ValueError("остаток не может быть отрицательным")

    material_id = max(
        (material["id"] for material in materials), default=0
    ) + 1
    material = {
        "id": material_id,
        "name": name.strip(),
        "unit": unit.strip(),
        "stock": stock,
    }
    materials.append(material)
    return material


def update_material(
    materials: list[dict],
    material_id: int,
    name: Optional[str] = None,
    unit: Optional[str] = None,
    stock: Optional[int] = None,
) -> dict:
    """Изменить переданные поля существующего материала."""
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    if name is not None:
        if not name.strip():
            raise ValueError("название материала не может быть пустым")
        material["name"] = name.strip()
    if unit is not None:
        if not unit.strip():
            raise ValueError("единица измерения не может быть пустой")
        material["unit"] = unit.strip()
    if stock is not None:
        if stock < 0:
            raise ValueError("остаток не может быть отрицательным")
        material["stock"] = stock
    return material


def delete_material(materials: list[dict], material_id: int) -> dict:
    """Удалить материал из справочника и вернуть удалённую запись."""
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    materials.remove(material)
    return material


def find_material(materials: list[dict], query: str) -> list[dict]:
    """Найти материалы по части названия без учёта регистра."""
    normalized_query = query.strip().lower()
    return [
        material
        for material in materials
        if normalized_query in str(material["name"]).lower()
    ]


def check_stock(
    materials: list[dict], material_id: int, quantity: int
) -> bool:
    """Проверить наличие требуемого количества материала на складе."""
    if quantity <= 0:
        raise ValueError("количество должно быть больше нуля")
    material = get_material(materials, material_id)
    if material is None:
        raise ValueError(f"материал с id={material_id} не найден")
    return int(material["stock"]) >= quantity


def filter_materials_by_stock(
    materials: list[dict], minimum: int
) -> list[dict]:
    """Вернуть материалы с остатком не меньше заданного."""
    if minimum < 0:
        raise ValueError("минимальный остаток не может быть отрицательным")
    suitable = (
        material
        for material in materials
        if int(material["stock"]) >= minimum
    )
    return list(suitable)


def sort_materials(
    materials: list[dict], by: str = "name", reverse: bool = False
) -> list[dict]:
    """Вернуть новый список материалов, отсортированный по полю."""
    if by not in {"name", "stock"}:
        raise ValueError("сортировка доступна только по name или stock")
    return sorted(
        materials,
        key=lambda material: material[by],
        reverse=reverse,
    )
