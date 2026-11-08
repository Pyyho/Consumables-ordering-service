"""Модель расходного материала Django ORM."""

from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from transliterate import translit


class Material(models.Model):
    name = models.CharField("Название", max_length=200)
    unit = models.CharField("Единица измерения", max_length=32)
    stock = models.PositiveIntegerField(
        "Остаток", default=0,
        help_text="Количество в единицах этого материала.",
    )
    slug = models.SlugField(
        "Адрес", max_length=100, unique=True, editable=False,
    )
    in_stock = models.GeneratedField(
        expression=models.Case(
            models.When(stock__gt=0, then=models.Value(True)),
            default=models.Value(False),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="В наличии",
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(translit(self.name, "ru", reversed=True))
            self.slug = f"{base[:60] or 'material'}-{uuid4().hex}"
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = {*kwargs["update_fields"], "slug"}
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "inventory:material_by_slug", kwargs={"slug": self.slug}
        )

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
