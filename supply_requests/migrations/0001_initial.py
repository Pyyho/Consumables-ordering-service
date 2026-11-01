import datetime

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


STATUSES = ("Новая", "На согласовании", "Утверждена", "В закупке",
            "Выполнена", "Отклонена", "Отменена")
CHOICES = [(status, status) for status in STATUSES]


class Migration(migrations.Migration):
    initial = True
    dependencies = [("inventory", "0001_initial"), ("staff", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="SupplyRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(
                    validators=[django.core.validators.MinValueValidator(1)],
                    verbose_name="Количество")),
                ("created", models.DateField(
                    db_index=True, default=datetime.date.today,
                    verbose_name="Дата создания")),
                ("status", models.CharField(
                    choices=CHOICES, default="Новая", max_length=32,
                    verbose_name="Статус")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="supply_requests", to="staff.employee",
                    verbose_name="Сотрудник")),
                ("material", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="supply_requests", to="inventory.material",
                    verbose_name="Материал")),
            ],
            options={"verbose_name": "Заявка", "verbose_name_plural": "Заявки",
                     "ordering": ["created", "pk"]},
        ),
        migrations.CreateModel(
            name="RequestHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("position", models.PositiveIntegerField(
                    verbose_name="Порядок события")),
                ("status", models.CharField(
                    choices=CHOICES, max_length=32, verbose_name="Статус")),
                ("request", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="status_events",
                    to="supply_requests.supplyrequest")),
            ],
            options={"verbose_name": "Событие заявки",
                     "verbose_name_plural": "История заявок",
                     "ordering": ["position", "pk"]},
        ),
        migrations.AddConstraint(
            model_name="supplyrequest",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="request_quantity_positive")),
        migrations.AddConstraint(
            model_name="supplyrequest",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=STATUSES),
                name="request_valid_status")),
        migrations.AddConstraint(
            model_name="requesthistory",
            constraint=models.UniqueConstraint(
                fields=("request", "position"),
                name="unique_request_history_position")),
        migrations.AddConstraint(
            model_name="requesthistory",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=STATUSES),
                name="history_valid_status")),
    ]
