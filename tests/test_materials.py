"""Тесты класса Material и функций коллекции материалов."""

import pytest

from models import Material
from models.materials import (
    add_material,
    check_stock,
    delete_material,
    filter_materials_by_stock,
    find_material,
    sort_materials,
    update_material,
)


def sample_materials() -> list[Material]:
    """Вернуть независимый набор тестовых объектов."""
    return [
        Material(1, "Бумага А4", "пачка", 25),
        Material(2, "Ручка", "шт", 120),
    ]


def test_material_creation_and_string() -> None:
    material = Material(1, "Бумага А4", "пачка", 25)
    assert material.id == 1
    assert material.name == "Бумага А4"
    assert material.stock == 25
    assert "Бумага А4" in str(material)


def test_material_from_data() -> None:
    material = Material.from_data(
        {"id": 3, "name": "Степлер", "unit": "шт", "stock": 4}
    )
    assert isinstance(material, Material)
    assert material.id == 3


def test_material_validates_stock() -> None:
    assert Material.validate_stock(0)
    assert not Material.validate_stock(-1)
    with pytest.raises(ValueError):
        Material(1, "Маркер", "шт", -1)


def test_material_has_stock() -> None:
    material = Material(1, "Бумага А4", "пачка", 25)
    assert material.has_stock(20)
    assert not material.has_stock(30)


def test_add_material_assigns_next_id() -> None:
    materials = sample_materials()
    material = add_material(materials, "Степлер", "шт", 3)
    assert material.id == 3
    assert materials[-1] is material


def test_find_filter_and_sort_materials() -> None:
    materials = sample_materials()
    assert [item.id for item in find_material(materials, "БУМАГА")] == [1]
    filtered = filter_materials_by_stock(materials, 30)
    assert [item.id for item in filtered] == [2]
    sorted_items = sort_materials(materials, by="stock")
    assert [item.id for item in sorted_items] == [1, 2]


def test_check_stock_uses_material_object() -> None:
    materials = sample_materials()
    assert check_stock(materials, 1, 20)
    assert not check_stock(materials, 1, 30)


def test_update_and_delete_material() -> None:
    materials = sample_materials()
    updated = update_material(materials, 1, name="Бумага A4+", stock=30)
    assert updated.name == "Бумага A4+"
    assert updated.stock == 30
    deleted = delete_material(materials, 2)
    assert deleted.name == "Ручка"
    assert len(materials) == 1
