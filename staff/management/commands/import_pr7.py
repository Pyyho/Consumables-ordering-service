from django.core.management.base import BaseCommand

from db.import_sqlite_to_orm import import_source


class Command(BaseCommand):
    help = "Перенести исходную SQLite ПР7 в текущую базу Django ORM."

    def add_arguments(self, parser):
        parser.add_argument("--source")

    def handle(self, *args, **options):
        result = import_source(options["source"])
        self.stdout.write(self.style.SUCCESS(f"Перенос завершён: {result}"))
