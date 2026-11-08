from django.db import migrations, models
from django.utils.text import slugify
from transliterate import translit


def populate_slugs(apps, schema_editor):
    material = apps.get_model("inventory", "Material")
    rows = material.objects.using(schema_editor.connection.alias)
    for item in rows.all().iterator():
        base = slugify(translit(item.name, "ru", reversed=True))
        item.slug = f"{base[:60] or 'material'}-{item.pk}"
        item.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="material",
            name="slug",
            field=models.SlugField(
                "Адрес", default="", editable=False, max_length=100,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="material",
            name="slug",
            field=models.SlugField(
                "Адрес", editable=False, max_length=100, unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="material",
            name="stock",
            field=models.PositiveIntegerField(
                "Остаток", default=0,
                help_text="Количество в единицах этого материала.",
            ),
        ),
        migrations.AddField(
            model_name="material",
            name="in_stock",
            field=models.GeneratedField(
                expression=models.Case(
                    models.When(stock__gt=0, then=models.Value(True)),
                    default=models.Value(False),
                ),
                output_field=models.BooleanField(),
                db_persist=True,
                verbose_name="В наличии",
            ),
        ),
    ]
