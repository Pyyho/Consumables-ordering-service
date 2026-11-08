# Сервис заказа расходных материалов

## ПР10 — администрирование и проверка ORM

После установки зависимостей и применения миграций создайте локального
суперпользователя, если его ещё нет:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Войдите на `http://127.0.0.1:8000/admin/`. В списке материалов можно искать
по названию или адресу, фильтровать по единице измерения и наличию, править
остаток прямо в таблице. В карточках материалов и сотрудников видны связанные
заявки. Сотрудников можно искать по ФИО, почте и подразделению. Заявки можно
искать по материалу, сотруднику или почте и фильтровать по дате, статусу,
материалу и сотруднику. Для справочников в форме заявки работает автопоиск.

При создании заявки и изменении количества или материала админка проверяет
остаток. Статусы и история сохраняются вместе. Массовое действие отменяет
только активные заявки, история доступна для просмотра. Для роли «Просмотр
каталога» создайте группу с разрешением `view_material` и назначьте её
пользователю с правом входа в админку (`is_staff`). Для редактирования
понадобится `change_material`. Модель сотрудника относится к справочнику,
а разрешения назначаются пользователям Django.

Миграция материалов заполняет уникальные латинские адреса существующих
записей. `get_absolute_url()` используется ссылкой «Посмотреть на сайте» в
админке. Старые числовые адреса также работают. Поле `in_stock` SQLite
вычисляет из `stock > 0`; оно обновляется при изменении остатка, включая
`QuerySet.update()`. Семь статусов оформлены через `TextChoices` с прежними
значениями. Выполненные, отклонённые и отменённые заявки исключаются из
`active()` и статистики активного спроса. Подбор материалов сравнивает
требуемое количество с остатком. Заявки не резервируют складские единицы.

Для анализа SQL запустите сервер с локальной панелью Debug Toolbar:

```powershell
$env:DJANGO_DEBUG_TOOLBAR = "1"
.\.venv\Scripts\python.exe manage.py runserver
# После остановки сервера
Remove-Item Env:DJANGO_DEBUG_TOOLBAR
```

На страницах заявок откройте вкладку SQL. При проверке без входа список,
страница 2 и страница 2 с фильтром выполняли по 4 запроса: подсчёт,
выборка страницы с JOIN и два справочника для фильтров. Карточка заявки
выполняла 2 запроса: заявка с материалом и сотрудником, затем история.
Дополнительные записи для измерения пагинации были созданы в транзакции
с откатом. `with_details()` централизует `select_related()` для списка,
поиска, карточки и статистики.

В Django Shell можно проверить вычисления на стороне БД без записи данных:

```python
from django.db.models import F
from inventory.models import Material
from supply_requests.models import SupplyRequest

Material.objects.annotate(next_stock=F("stock") + 1).values("name", "next_stock")
requests = SupplyRequest.objects.active().with_details()
print(requests.query)
print(requests.explain())
```

Индивидуальный проект: каталог складских материалов, сотрудники и заявки
на снабжение. В ПР9 веб-приложение переведено с SQL-запросов ПР7 на Django ORM.
Шаблоны ПР6, адреса страниц и прежние сценарии сохранены.

## Запуск

Команды выполняются из корня проекта в терминале VS Code или PyCharm.
Для Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py import_pr7
.\.venv\Scripts\python.exe manage.py runserver
```

Если `.venv` уже существует, используйте его интерпретатор; создавать окружение
повторно не нужно. Python 3.12 также поддерживается. Откройте
<http://127.0.0.1:8000/>. Сервер останавливается сочетанием `Ctrl+C`.
В IDE выберите `.venv\Scripts\python.exe` как интерпретатор проекта.

## Данные и перенос из ПР7

| Назначение | Файл |
| --- | --- |
| Рабочая база Django, включая предметные модели ПР9 | `db.sqlite3` |
| Исходная предметная база ПР7 | `data/consumables.sqlite` |
| Автоматические резервные копии | `data/backups/` |
| Исходные данные консольной версии | `data/*.json` |
| Переносимый снимок предметных данных ПР9 | `fixtures/pr9_initial.json` |

`DATABASES` указывает на `db.sqlite3`. Таблицы моделей создаёт `migrate`.
Команда `import_pr7` открывает источник только для чтения, проверяет целостность
и внешние ключи, делает резервную копию и переносит данные через ORM в одной
транзакции. Сохраняются идентификаторы материалов, сотрудников и заявок,
внешние ключи, даты, статусы и порядок истории. У событий истории источник
имеет составной ключ `(request_id, position)`; Django добавляет собственный ID.

Повторный импорт обновляет записи с теми же ключами через `update_or_create()`;
дубликаты не появляются, дополнительные записи в Django не удаляются.
Учитывайте, что повторный импорт перезапишет изменения совпадающих записей
данными источника. Изменение исходной SQLite или JSON само по себе сайт
не обновляет. При ошибке перенос целиком откатывается.

```powershell
.\.venv\Scripts\python.exe db/inspect_source_db.py
.\.venv\Scripts\python.exe manage.py import_pr7 --source data/consumables.sqlite
# Альтернативный запуск того же переноса:
.\.venv\Scripts\python.exe -m db.import_sqlite_to_orm
```

Инспектор показывает таблицы, столбцы, количество строк и внешние ключи.
Исходный набор: 4 материала, 3 сотрудника, 3 заявки и 5 событий истории.
Если база ПР7 отсутствует, её можно создать из сохранённых JSON:

```powershell
.\.venv\Scripts\python.exe -m db.import_json
```

Это отдельная операция подготовки источника; обычному запуску сайта она
не нужна. Рабочая база и резервные копии исключены из Git.

## Модели ПР9

| Приложение и модель | Поля и связи |
| --- | --- |
| `inventory.Material` | название, единица измерения, неотрицательный остаток |
| `staff.Employee` | имя, уникальный email без учёта регистра, подразделение |
| `supply_requests.SupplyRequest` | материал, сотрудник, положительное количество, дата, статус |
| `supply_requests.RequestHistory` | заявка, порядковый номер события, статус |

Материал и сотрудник связаны с заявками отношениями «один ко многим».
`ForeignKey(..., on_delete=PROTECT)` защищает используемые справочники от
удаления. История относится к заявке через `CASCADE` и удаляется вместе с ней.
Пара `(request, position)` уникальна. Определены `__str__`, русские названия
и порядок сортировки `Meta`; обязательные ограничения проверяются также в БД.
Все четыре модели зарегистрированы в Django Admin.

Статусы: «Новая», «На согласовании», «Утверждена», «В закупке», «Выполнена»,
«Отклонена», «Отменена». Последние три считаются завершёнными.
Создание заявки проверяет остаток, но не списывает и не резервирует материалы,
как в прежней реализации. Методы `create_for()`, `change_status()` и `cancel()`
сохраняют изменения и историю атомарно. Повторная отмена не дублирует событие.

## Страницы и запросы

| URL | Назначение |
| --- | --- |
| `/` | главная страница и навигация |
| `/materials/` | каталог материалов |
| `/materials/<id>/` | карточка материала |
| `/materials/available/?quantity=5` | подбор по складскому остатку |
| `/requests/` | все заявки, фильтры, сортировка, страницы |
| `/requests/active/` | активные заявки с теми же фильтрами |
| `/requests/<id>/` | карточка заявки, связанные объекты и история |
| `/requests/search/?date=2026-09-20` | поиск по дате создания |
| `/requests/employees/` | справочник сотрудников |
| `/requests/statistics/` | статистика снабжения |

Список заявок принимает GET-параметры `date`, `material`, `employee`, `status`,
`q`, `sort`, `page`. Текстовый поиск `q` проверяет название материала, имя,
email и подразделение сотрудника. Фильтры применяются одновременно.
Пример: `/requests/?material=1&status=Новая&sort=newest`.

Допустимые сортировки: `date`, `newest`, `material`, `employee`, `status`.
Остальные значения возвращают стандартную сортировку по дате и ID.
`Paginator` выводит по 5 заявок; ссылки через `{% querystring %}` сохраняют
все фильтры. Для исходных трёх заявок страница одна. Некорректный номер
страницы обрабатывает `get_page()`: текст даёт первую, выход за границы —
последнюю. Ошибочные даты, ID фильтров, статусы и количество дают понятное
сообщение и HTTP 400; отсутствующая карточка — HTTP 404.

Веб-представления используют только ORM. Для связей заявок применяется
`select_related("material", "employee")`, чтобы не выполнять запрос на каждую
строку. Статистика использует `aggregate()`, `annotate()`, `Count`, `Sum`,
`Avg`, `Min`, `Max`, условные подсчёты, группировку по подразделениям,
`values_list()` и `exclude()` для материалов без активных заявок. Последние
заявки выбираются срезом `[:5]`. Спрос считается отдельно для каждого материала,
без сложения разных единиц измерения; нулевые группы сохраняются.

## CRUD и другие операции через Django shell

Веб-формы изменения данных в ПР9 не требуются. Для демонстрации ORM:

```powershell
.\.venv\Scripts\python.exe manage.py shell
```

```python
from datetime import date
from django.db.models import F, Q, Count, Sum
from inventory.models import Material
from staff.models import Employee
from supply_requests.models import SupplyRequest

# CREATE: отдельные демонстрационные записи.
m = Material.objects.create(name="Папка демонстрационная", unit="шт.", stock=20)
e = Employee.objects.create(
    name="Демонстрационный сотрудник",
    email="orm-demo@example.com", department="Снабжение",
)
r = SupplyRequest.create_for(e, m, 2, created=date.today())

# READ / фильтры / объединение условий / сортировка / связанные данные.
Material.objects.get(pk=m.pk)
Material.objects.filter(stock__gte=5).order_by("name")
SupplyRequest.objects.select_related("material", "employee").filter(
    Q(material__name__icontains="папка") | Q(employee__department="Снабжение")
)
SupplyRequest.objects.active().exclude(employee=e)
SupplyRequest.objects.order_by("-created", "-pk")[:5]
SupplyRequest.objects.values_list("material_id", flat=True)
SupplyRequest.objects.values("material_id").annotate(total=Sum("quantity"))
Material.objects.aggregate(total=Count("id"))

# UPDATE: выражение F и сохранение изменения статуса вместе с историей.
Material.objects.filter(pk=m.pk).update(stock=F("stock") + 3)
m.refresh_from_db()
r.change_status("Утверждена")
r.cancel()
list(r.status_events.values_list("status", flat=True))

# DELETE: сначала заявка с историей, затем связанные справочники.
r.delete()
e.delete()
m.delete()
```

`get()` для отсутствующего объекта вызывает `DoesNotExist`, для нескольких —
`MultipleObjectsReturned`; `filter()` возвращает QuerySet, в том числе пустой.
`update()` не вызывает методы модели: для смены статуса используйте методы
заявки, чтобы сохранить историю. Перед `save()` вручную созданного объекта
можно вызвать `full_clean()`. Удаление используемого материала/сотрудника
вызывает `ProtectedError`.

## Фикстуры

Для новой базы после миграций можно загрузить снимок вместо импорта ПР7:

```powershell
.\.venv\Scripts\python.exe manage.py loaddata fixtures/pr9_initial.json
```

Сохранение текущих предметных данных:

```powershell
.\.venv\Scripts\python.exe -X utf8 manage.py dumpdata inventory staff supply_requests --indent 2 --output fixtures/pr9_initial.json
```

Фикстура содержит предметные записи и связи, без пользователей администратора.
Загрузка записей с совпадающими PK обновляет их; выполняйте её осознанно.
Для админ-панели создайте пользователя командой `manage.py createsuperuser`
и откройте `/admin/`.

## Проверки

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flake8 .
```

Тесты изолированы от рабочей базы через pytest-django. Проверяются прежние
сценарии, импорт и его повторение/откат, сохранность источника, связи и
ограничения, CRUD, история отмены, оптимизация связанных запросов, фильтры,
сортировка, пагинация, статистика и цикл `dumpdata`/`loaddata`.

## Сохранённые предыдущие работы и Git

Ветка ПР7 называется `pr7-sql` (через дефис). Она объединена с `main`;
ПР9 выполняется в `main`. ПР6 доступна в истории на коммите `38f1426`,
ПР7 — в ветке `pr7-sql` на `8fed913`. Отправка локальных изменений на GitHub
выполняется отдельно.

Консольная версия ПР3 запускается `python main.py`, использует пакет `models/`
с обычными Python-классами и JSON-хранилище. Она сохранена для прежних работ.
Модули `db/database.py`, `db/queries.py`, `db/import_json.py` и `sql/` относятся
к SQL-реализации ПР7; проверить её запросы можно командой
`python -m db.check_queries`. Веб-представления ПР9 их не вызывают.

Репозиторий: <https://github.com/Pyyho/Consumables-ordering-service>.
