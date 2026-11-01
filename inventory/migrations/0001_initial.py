from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Material",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("name", models.CharField(max_length=200,
                                          verbose_name="Название")),
                ("unit", models.CharField(max_length=32,
                                          verbose_name="Единица измерения")),
                ("stock", models.PositiveIntegerField(default=0,
                                                      verbose_name="Остаток")),
            ],
            options={
                "verbose_name": "Материал",
                "verbose_name_plural": "Материалы",
                "ordering": ["name", "pk"],
                "constraints": [
                    models.CheckConstraint(condition=~models.Q(name=""),
                                           name="material_name_not_empty"),
                    models.CheckConstraint(condition=~models.Q(unit=""),
                                           name="material_unit_not_empty"),
                ],
            },
        ),
    ]
