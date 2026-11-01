"""Модель сотрудника, не связанная с учётной записью Django auth."""

from django.db import models


class Employee(models.Model):
    name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("Электронная почта", unique=True,
                              db_collation="nocase")
    department = models.CharField("Подразделение", max_length=200)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def __str__(self) -> str:
        return f"{self.name} — {self.department}"
