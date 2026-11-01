from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False,
                                           verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="ФИО")),
                ("email", models.EmailField(
                    db_collation="nocase", max_length=254, unique=True,
                    verbose_name="Электронная почта")),
                ("department", models.CharField(
                    max_length=200, verbose_name="Подразделение")),
            ],
            options={"verbose_name": "Сотрудник",
                     "verbose_name_plural": "Сотрудники",
                     "ordering": ["name", "pk"]},
        ),
    ]
