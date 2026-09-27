"""Совместимый импорт функций материалов из объектной модели ПР3."""

from models.materials import (
    Material,
    add_material,
    check_stock,
    delete_material,
    filter_materials_by_stock,
    find_material,
    get_material,
    show_materials,
    sort_materials,
    update_material,
)

__all__ = [
    "Material",
    "add_material",
    "check_stock",
    "delete_material",
    "filter_materials_by_stock",
    "find_material",
    "get_material",
    "show_materials",
    "sort_materials",
    "update_material",
]
