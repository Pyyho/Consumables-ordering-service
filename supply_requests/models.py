"""ORM-модели заявок и истории с сохранением правил предметной области."""

from datetime import date

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Max, Q

from models.requests import FINAL_STATUSES, VALID_STATUSES


STATUS_CHOICES = [(status, status) for status in VALID_STATUSES]


class SupplyRequestQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(status__in=FINAL_STATUSES)


class SupplyRequest(models.Model):
    material = models.ForeignKey(
        "inventory.Material", on_delete=models.PROTECT,
        related_name="supply_requests", verbose_name="Материал",
    )
    employee = models.ForeignKey(
        "staff.Employee", on_delete=models.PROTECT,
        related_name="supply_requests", verbose_name="Сотрудник",
    )
    quantity = models.PositiveIntegerField(
        "Количество", validators=[MinValueValidator(1)]
    )
    created = models.DateField("Дата создания", default=date.today,
                               db_index=True)
    status = models.CharField("Статус", max_length=32, choices=STATUS_CHOICES,
                              default="Новая")

    objects = SupplyRequestQuerySet.as_manager()

    class Meta:
        ordering = ["created", "pk"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0),
                                   name="request_quantity_positive"),
            models.CheckConstraint(condition=Q(status__in=VALID_STATUSES),
                                   name="request_valid_status"),
        ]

    @property
    def is_cancelled(self) -> bool:
        return self.status == "Отменена"

    @property
    def material_name(self) -> str:
        return self.material.name

    @property
    def employee_name(self) -> str:
        return self.employee.name

    @property
    def unit(self) -> str:
        return self.material.unit

    @property
    def department(self) -> str:
        return self.employee.department

    @property
    def created_display(self) -> str:
        return self.created.strftime("%d.%m.%Y")

    @classmethod
    @transaction.atomic
    def create_for(cls, employee, material, quantity, created=None):
        """Проверить остаток и создать заявку вместе с первым событием."""
        material = type(material).objects.select_for_update().get(
            pk=material.pk
        )
        if not material.has_stock(quantity):
            raise ValueError("На складе недостаточно материала.")
        item = cls(employee=employee, material=material, quantity=quantity,
                   created=created or date.today())
        item.full_clean()
        item.save()
        item.status_events.create(position=0, status=item.status)
        return item

    @transaction.atomic
    def _set_status(self, new_status: str, *, require_open=False) -> None:
        if new_status not in VALID_STATUSES:
            raise ValueError("Недопустимый статус.")
        current = type(self).objects.select_for_update().get(pk=self.pk)
        if require_open and current.status in FINAL_STATUSES:
            raise ValueError("Заявку в конечном статусе нельзя отменить.")
        if current.status != new_status:
            current.status = new_status
            current.save(update_fields=["status"])
            maximum = current.status_events.aggregate(value=Max("position"))[
                "value"
            ]
            position = 0 if maximum is None else maximum + 1
            current.status_events.create(position=position, status=new_status)
        self.status = current.status

    def change_status(self, new_status: str) -> None:
        self._set_status(new_status)

    def cancel(self) -> None:
        self._set_status("Отменена", require_open=True)

    def __str__(self) -> str:
        return f"Заявка №{self.pk}: {self.material} — {self.status}"


class RequestHistory(models.Model):
    request = models.ForeignKey(SupplyRequest, on_delete=models.CASCADE,
                                related_name="status_events")
    position = models.PositiveIntegerField("Порядок события")
    status = models.CharField("Статус", max_length=32, choices=STATUS_CHOICES)

    class Meta:
        ordering = ["position", "pk"]
        verbose_name = "Событие заявки"
        verbose_name_plural = "История заявок"
        constraints = [
            models.UniqueConstraint(fields=["request", "position"],
                                    name="unique_request_history_position"),
            models.CheckConstraint(condition=Q(status__in=VALID_STATUSES),
                                   name="history_valid_status"),
        ]

    def __str__(self) -> str:
        return f"№{self.request_id}, {self.position}: {self.status}"
