# Сервис заказа расходных материалов

Приложение для ведения справочника расходных материалов и обработки заявок
сотрудников организации. Консольная версия на объектной модели ПР3 сохранена,
в ПР5 добавлен веб-интерфейс на Django 5.2, а в ПР6 все пять страниц переведены
на Django Template Language (DTL). В ПР7 веб-часть получает данные из отдельной
базы SQLite через стандартную библиотеку `sqlite3`, без Django ORM.

## Возможности

В веб-интерфейсе ПР7 реализованы:

- главная страница с навигацией;
- список расходных материалов из SQLite;
- страница отдельного материала по числовому идентификатору;
- отображение складского остатка и статуса наличия;
- список всех и активных заявок из SQLite;
- страница отдельной заявки со связанными сотрудником и материалом;
- отображение статуса и истории статусов заявки;
- подбор материалов по требуемому количеству;
- поиск заявок по дате создания;
- справочник сотрудников и статистика снабжения;
- ответ с кодом 404 для несуществующего материала или заявки.

Консольная версия по-прежнему поддерживает создание, изменение, поиск и удаление
материалов, работу с сотрудниками, создание заявок, изменение статусов и сохранение
данных в JSON.

## Используемые технологии

- Python 3;
- Django 5.2;
- Django Template Language (DTL);
- HTML и CSS;
- JavaScript;
- Bootstrap 5.3 через CDN;
- SQLite и стандартная библиотека Python `sqlite3`;
- JSON как источник первоначального импорта и хранилище консольной версии;
- pytest для автоматизированных тестов;
- flake8 для проверки стиля кода.

## Предметная область

Основные сущности проекта:

- `Material` — расходный материал с единицей измерения и складским остатком;
- `Employee` — сотрудник организации, создающий заявку;
- `SupplyRequest` — заявка, которая связывает сотрудника и материал.

Эти классы сохранены для консольной версии и проверки данных при импорте.
В ПР7 веб-представления получают именованные строки `sqlite3.Row` из SQL-запросов,
передают их через контекст в шаблоны и вызывают `render()`. Django ORM пока
не используется. Веб-часть только читает SQLite, а консольная версия работает
с JSON. Изменения JSON после импорта автоматически в SQLite не попадают.

## Страницы веб-интерфейса

| URL | View-функция | Назначение |
| --- | --- | --- |
| `/` | `homepage.views.index()` | описание сервиса и навигация |
| `/materials/` | `inventory.views.materials()` | список материалов |
| `/materials/<int:material_id>/` | `inventory.views.material_detail()` | карточка материала |
| `/materials/available/?quantity=5` | `inventory.views.available_materials()` | подбор по складскому остатку |
| `/requests/` | `supply_requests.views.requests()` | список заявок |
| `/requests/<int:request_id>/` | `supply_requests.views.request_detail()` | карточка заявки |
| `/requests/active/` | `supply_requests.views.active_requests()` | незавершённые заявки |
| `/requests/search/?date=2026-09-20` | `supply_requests.views.requests_by_date()` | поиск по дате создания |
| `/requests/employees/` | `supply_requests.views.employees()` | сотрудники |
| `/requests/statistics/` | `supply_requests.views.statistics()` | статистика снабжения |

Маршруты распределены по приложениям и подключены через `include()` в
`consumables_service/urls.py`. Динамические адреса используют конвертер `int`.

## Структура проекта

```text
Consumables-ordering-service/
├── manage.py
├── main.py
├── storage.py
├── utils.py
├── requirements.txt
├── db/
│   ├── database.py
│   ├── import_json.py
│   ├── queries.py
│   └── check_queries.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── consumables_service/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── homepage/
│   ├── templates/homepage/index.html
│   ├── static/homepage/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/logo.svg
│   ├── urls.py
│   └── views.py
├── inventory/
│   ├── templates/inventory/
│   │   ├── material_list.html
│   │   ├── material_detail.html
│   │   ├── available.html
│   │   └── includes/material_card.html
│   ├── urls.py
│   └── views.py
├── supply_requests/
│   ├── templates/supply_requests/
│   │   ├── request_list.html
│   │   ├── request_detail.html
│   │   ├── search.html
│   │   ├── statistics.html
│   │   ├── employees.html
│   │   └── includes/request_status.html
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── base.html
│   └── includes/navigation.html
├── models/
│   ├── materials.py
│   ├── requests.py
│   └── users.py
├── data/
│   ├── materials.json
│   ├── employees.json
│   ├── requests.json
│   └── consumables.sqlite
└── tests/
    ├── test_materials.py
    ├── test_requests.py
    ├── test_storage.py
    ├── test_database.py
    ├── test_users.py
    └── test_web.py
```

`consumables_service/` содержит настройки Django и маршрутизацию верхнего уровня.
Приложение `homepage` отвечает за главную страницу и общие статические ресурсы,
`inventory` — за материалы, `supply_requests` — за заявки. Пакет `models/` и
JSON-хранилище относятся к объектной модели ПР3 и используются консолью
и импортом. Веб-данные выбираются SQL-запросами из `data/consumables.sqlite`.

## Шаблоны Django и контекст

Общая HTML-структура находится в `templates/base.html`: метатеги, Bootstrap,
собственный CSS, навигация, основной контейнер, подвал и JavaScript. Все
дочерних страниц используют `{% extends "base.html" %}` и переопределяют
`{% block title %}` и `{% block content %}`. В `settings.py` указано
`TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]`; `APP_DIRS` включён.

Повторяющиеся фрагменты подключаются через `{% include %}`:

- `includes/navigation.html` — навигация на всех страницах;
- `inventory/includes/material_card.html` — карточка материала в списке;
- `supply_requests/includes/request_status.html` — общий статус в списке и карточке заявки.

Контекст списка материалов содержит `materials`, карточки — `material` и
`available`. Для заявок используются `supply_requests` и `supply_request`.
Значения — строки `sqlite3.Row` с доступом по именам полей.
В шаблонах данные выводятся через `{{ material.name }}` и
`{{ supply_request.employee_name }}`. Связанные названия получены через JOIN.
Автоматическое экранирование DTL включено. История заявки передаётся отдельно
в `history` из таблицы `request_history`.

Коллекции перебираются через `{% for %}` с веткой `{% empty %}`. Конструкции
`{% if %}` обрабатывают отсутствие объекта, наличие материала и статусы заявок.
Если объект не найден, view передаёт `None` в тот же шаблон деталей и задаёт
`status=404`, а сообщение пользователю выбирает шаблон.

Фильтры `length` показывают число материалов и заявок, `default:"Без названия"`
задаёт резервную подпись. В ПР7 дата хранится как ISO-текст, а поле
`created_display` форматируется запросом через `strftime('%d.%m.%Y', created)`.
Остаток для подбора проверяется условием `WHERE stock >= :quantity`.

Ссылки формируются тегом `{% url %}` с существующими пространствами имён:
`homepage:index`, `inventory:materials`, `inventory:material_detail`,
`supply_requests:requests`, `supply_requests:request_detail`.

## Статические файлы

Ресурсы размещены в `homepage/static/homepage/`:

- `css/style.css` — оформление шапки, карточек материалов, статусов и таблицы;
- `img/logo.svg` — логотип коробки расходных материалов;
- `js/main.js` — установка текущего года в подвале страницы.

Используются `{% load static %}` и `{% static %}`. Логотип подключён в общей
навигации, CSS и JavaScript — в базовом шаблоне. Год также выводится серверным
тегом `{% now "Y" %}` на случай отключённого JavaScript.

Проверка поиска ресурсов:

```bash
python manage.py findstatic homepage/css/style.css homepage/js/main.js homepage/img/logo.svg
```

## Установка

Для Django 5.2 используйте Python 3.10 или новее (для учебной работы
рекомендуется Python 3.11–3.13). Откройте терминал в корне проекта.

Создайте и активируйте виртуальное окружение, затем установите зависимости:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Проверить установленную версию Django:

```bash
python -m django --version
```

## Запуск веб-версии

В поставке есть база с импортированными данными. Если её нет, создайте схему
и импортируйте исходные JSON (команда импорта создаёт схему автоматически):

```bash
python -m db.database
python -m db.import_json
```

Импорт в непустую базу остановится без перезаписи данных. Явная замена
предметных таблиц из JSON выполняется только при необходимости:

```bash
python -m db.import_json --replace
```

Замена затрагивает только `data/consumables.sqlite`. При ошибке транзакция
откатывается целиком. JSON и служебная база Django не изменяются.
Перед первым запуском также примените встроенные миграции Django:

```bash
python manage.py migrate
python manage.py check
python manage.py runserver
```

После запуска откройте `http://127.0.0.1:8000/`.

## Запуск консольной версии

```bash
python main.py
```

## Тестирование и проверка кода

```bash
pytest -v
flake8 .
```

Тесты проверяют объектную модель ПР3, JSON-загрузку и сохранение, маршруты Django,
данные на HTML-страницах, связи объектов и ответы 404, наследование шаблонов,
контекст, включаемые фрагменты, все семь статусов и поиск статических файлов.
SQL-тесты проверяют внешние ключи, ограничения, JOIN, агрегаты, группировки,
HAVING, подзапросы, историю и атомарный откат импорта. Веб-тесты создают
собственные JSON и SQLite во временном каталоге: рабочая база не используется.
Файл `.flake8` исключает виртуальные
окружения и временные файлы из проверки.

## Перенос сценариев ПР3 в ПР5

| Сценарий ПР3 | Реализация на этапе ПР5 |
| --- | --- |
| Просмотр материалов | список `/materials/` |
| Поиск материала по ID | `get_material()` в карточке материала |
| Проверка остатка | `Material.has_stock(1)` для статуса наличия |
| Просмотр заявок | список `/requests/` |
| Поиск заявки по ID | `get_request()` в карточке заявки |
| Просмотр связей и истории | сотрудник, материал и статусы в карточке заявки |
| Поиск, фильтрация, сортировка | доступны в консоли, веб-формы добавятся позднее |
| Создание, изменение, удаление | доступны в консоли, веб-формы добавятся позднее |

Заявка связывает `Employee` и `Material` через атрибуты `employee` и `material`.
`storage.py` восстанавливает эти ссылки из `employee_id` и `material_id`.
Собственные `models.py` Django-приложений остаются без ORM-моделей.
`db.sqlite3` содержит только служебные таблицы Django, а не материалы и заявки.
В ПР6 функция `page()` и генерация HTML-строк из views удалены. Общая структура
вынесена в `base.html`, ссылки строятся в шаблонах с помощью `{% url %}`.

Для самопроверки откройте все пять URL из таблицы выше, затем
`/materials/999/` и `/requests/999/`: они должны вернуть 404. При нулевом
остатке карточка показывает «Нет на складе»; пустые списки выводят пояснение.
Стили Bootstrap загружаются через CDN, для полного оформления нужен интернет.

## Фиксация результата в Git

На начало ПР7 `main` содержит ПР6, коммит `38f1426` (`Final PR6`).
Изменения ПР7 оставлены в рабочем дереве, чтобы вы сохранили их в новой ветке.
Из корня проекта выполните команды по порядку:

```bash
git status
git switch -c codex/pr7-sql
git diff
git add .
git commit -m "PR7: add SQLite database and SQL queries"
git push -u origin codex/pr7-sql
```

Создание ветки перенесёт в неё незакоммиченные изменения. Сначала завершите
коммит в новой ветке; затем для защиты переключайтесь:

```bash
git switch main
python manage.py runserver
```

После показа ПР6 остановите сервер (`Ctrl+C`), затем:

```bash
git switch codex/pr7-sql
python manage.py runserver
```

`git merge` для раздельной защиты не нужен. Отправка ветки на GitHub
не объединяет её с `main`. Дождитесь чистого `git status` перед переключением.

## Текущее состояние

ПР7: веб-слой читает SQLite через `sqlite3`, сохраняет шаблоны ПР6 и содержит
17 именованных SQL-запросов. В следующих работах планируются Django ORM,
формы изменения объектов, авторизация и REST API.

## База данных ПР7

Предметная база — `data/consumables.sqlite`. Её не следует путать с
`db.sqlite3`, где остаются только служебные таблицы Django.

| Таблица | Поля и типы | Ключи |
| --- | --- | --- |
| `materials` | `id INTEGER`, `name TEXT`, `unit TEXT`, `stock INTEGER` | PK `id` |
| `employees` | `id INTEGER`, `name TEXT`, `email TEXT`, `department TEXT` | PK `id`, UNIQUE `email` |
| `supply_requests` | `id INTEGER`, `material_id INTEGER`, `employee_id INTEGER`, `quantity INTEGER`, `created TEXT`, `status TEXT` | PK `id`, FK на материал и сотрудника |
| `request_history` | `request_id INTEGER`, `position INTEGER`, `status TEXT` | составной PK `(request_id, position)`, FK на заявку |

Остаток неотрицательный, количество положительное, основные поля обязательны,
статус ограничен семью значениями. Дата хранится в ISO-формате `YYYY-MM-DD`.
История вынесена в отдельную таблицу, чтобы не терять её при импорте.
Внешние ключи включаются в каждом соединении (`PRAGMA foreign_keys = ON`),
`row_factory = sqlite3.Row` даёт доступ к столбцам по именам.

Схема: `sql/schema.sql`. Импорт: `db/import_json.py`, где данные проверяются
существующими классами, вставляются через `executemany()` с параметрами `?`,
а ошибка откатывает транзакцию. Читающие соединения закрываются через
`contextlib.closing`. Веб-слой открывает SQLite в режиме чтения, поэтому не
создаёт пустую базу по ошибочному пути и не изменяет данные при GET-запросах.

### Запросы и страницы

`sql/queries.sql` — единый источник запросов, которые читает `db/queries.py`.
Каждый блок имеет комментарий `-- name: ...`. Пользовательские значения
передаются отдельно (`:quantity`, `:created`, `:id`) без строковой подстановки.

| № | Имя запроса | Назначение и использование |
| --- | --- | --- |
| 1 | `materials_list` | SELECT и сортировка: каталог |
| 2 | `employees_list` | SELECT и сортировка: сотрудники |
| 3 | `materials_available` | WHERE: подбор по количеству |
| 4 | `material_detail` | WHERE: карточка материала |
| 5 | `requests_all` | JOIN трёх таблиц: все заявки |
| 6 | `requests_active` | JOIN + WHERE: активные заявки |
| 7 | `requests_on_date` | JOIN + WHERE: поиск по дате |
| 8 | `request_detail` | JOIN + WHERE: карточка заявки |
| 9 | `request_history` | WHERE + ORDER BY: история заявки |
| 10 | `material_summary` | COUNT: сводка склада |
| 11 | `request_summary` | COUNT: сводка заявок |
| 12 | `material_statistics` | LEFT JOIN, SUM, GROUP BY: спрос по материалам |
| 13 | `employee_statistics` | LEFT JOIN, COUNT, GROUP BY: заявки сотрудников |
| 14 | `popular_materials` | GROUP BY + HAVING: повышенный спрос |
| 15 | `department_statistics` | GROUP BY + HAVING: активные подразделения |
| 16 | `recent_requests` | JOIN, ORDER BY, LIMIT, OFFSET: последние заявки |
| 17 | `materials_without_active` | подзапрос NOT EXISTS: материалы без активных заявок |

Запросы 10–17 отображаются на `/requests/statistics/`; материалы и сотрудники
с нулём активных заявок сохраняются в группировках благодаря LEFT JOIN.
Активные заявки — все, кроме выполненных, отклонённых и отменённых.
Общие количества разных единиц измерения не складываются: спрос считается
для каждого материала отдельно. Создание заявки не резервирует остаток,
как и в ПР3; поиск наличия использует текущий складской остаток.

Вариант «свободные помещения на дату» из учебного Roomly адаптирован к теме:
материалы подбираются по количеству, а дата используется для поиска созданных
заявок. Искусственная модель бронирования материалов не вводится.

Проверить все 17 запросов средствами стандартной библиотеки:

```bash
python -m db.check_queries
```

Если установлен SQLite CLI, база открывается командой
`sqlite3 data/consumables.sqlite`. В VS Code её можно открыть SQLite Viewer.
Для SQL-параметров в CLI сначала задайте значения (например,
`.parameter set :quantity 5`), затем выполните соответствующий SELECT.

Для демонстрации источника данных измените название в SQLite:

```sql
UPDATE materials SET name = 'Бумага А4 — обновлено' WHERE id = 1;
```

После обновления страницы новое название появится на сайте без повторного
импорта. Сохранённые JSON останутся прежними.

## Репозиторий

https://github.com/Pyyho/Consumables-ordering-service
