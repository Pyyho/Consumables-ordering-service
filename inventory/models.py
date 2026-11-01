"""Модель расходного материала Django ORM."""

from django.core.exceptions import ValidationError
from django.db import models


class Material(models.Model):
    name = models.CharField("Название", max_length=200)
    unit = models.CharField("Единица измерения", max_length=32)
    stock = models.PositiveIntegerField("Остаток", default=0)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""),
                                   name="material_name_not_empty"),
            models.CheckConstraint(condition=~models.Q(unit=""),
                                   name="material_unit_not_empty"),
        ]

    def clean(self) -> None:
        self.name = self.name.strip()
        self.unit = self.unit.strip()
        if not self.name or not self.unit:
            raise ValidationError("Название и единица не могут быть пустыми.")

    def has_stock(self, quantity: int) -> bool:
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля.")
        return self.stock >= quantity

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"
