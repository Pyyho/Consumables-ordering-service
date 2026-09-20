"""Тесты функций справочника материалов."""

import pytest

from materials import (
    add_material,
    check_stock,
    delete_material,
    filter_materials_by_stock,
    find_material,
    sort_materials,
    update_material,
)


def sample_materials() -> list[dict]:
    """Вернуть независимый набор тестовых материалов."""
    return [
        {"id": 1, "name": "Бумага А4", "unit": "пачка", "stock": 25},
        {"id": 2, "name": "Ручка", "unit": "шт", "stock": 120},
    ]


def test_add_material_assigns_next_id() -> None:
    materials = sample_materials()
    material = add_material(materials, "Степлер", "шт", 3)
    assert material["id"] == 3
    assert len(materials) == 3


def test_find_material_is_case_insensitive() -> None:
    found = find_material(sample_materials(), "БУМАГА")
    assert [material["id"] for material in found] == [1]


def test_check_stock() -> None:
    assert check_stock(sample_materials(), 1, 20)
    assert not check_stock(sample_materials(), 1, 30)


def test_filter_and_sort_materials() -> None:
    materials = filter_materials_by_stock(sample_materials(), 30)
    assert [material["id"] for material in materials] == [2]
    sorted_items = sort_materials(sample_materials(), by="stock")
    assert [material["id"] for material in sorted_items] == [1, 2]


def test_add_material_rejects_negative_stock() -> None:
    with pytest.raises(ValueError):
        add_material([], "Маркер", "шт", -1)


def test_update_and_delete_material() -> None:
    materials = sample_materials()
    updated = update_material(materials, 1, name="Бумага A4+", stock=30)
    assert updated["name"] == "Бумага A4+"
    assert updated["stock"] == 30
    deleted = delete_material(materials, 2)
    assert deleted["name"] == "Ручка"
    assert len(materials) == 1
