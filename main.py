from datetime import date

# Справочник материалов (имитация базы данных)
materials = [
    {"id": 1, "name": "Бумага А4", "unit": "пачка", "stock": 25},
    {"id": 2, "name": "Ручка шариковая", "unit": "шт", "stock": 120},
    {"id": 3, "name": "Картридж для принтера", "unit": "шт", "stock": 4},
]

# Список заявок
requests = []

# Допустимые статусы заявки
VALID_STATUSES = ["Новая", "На согласовании", "Утверждена", "В закупке", "Выполнена", "Отклонена"]

# Счётчик для номеров заявок
next_request_id = 1


# 1. Создание заявки
def create_request(employee, material_id, quantity):
    global next_request_id

    material = next((m for m in materials if m["id"] == material_id), None)
    if material is None:
        return "Ошибка: материал с таким id не найден"

    if quantity <= 0:
        return "Ошибка: количество должно быть больше нуля"

    new_request = {
        "id": next_request_id,
        "employee": employee,
        "material": material["name"],
        "quantity": quantity,
        "created": date.today(),
        "status": "Новая",
        "history": ["Новая"],
    }
    requests.append(new_request)
    next_request_id += 1

    return f"Заявка №{new_request['id']} создана сотрудником {employee}"


# 2. Просмотр списка заявок с фильтром по статусу
def show_requests(status=None):
    filtered = requests if status is None else [r for r in requests if r["status"] == status]

    if not filtered:
        return "Заявок не найдено"

    lines = []
    for r in filtered:
        lines.append(
            f"№{r['id']} | {r['employee']} | {r['material']} — {r['quantity']} | "
            f"{r['created']} | Статус: {r['status']}"
        )
    return "\n".join(lines)


# 3. Изменение статуса заявки
def change_status(request_id, new_status):
    if new_status not in VALID_STATUSES:
        return f"Ошибка: недопустимый статус '{new_status}'"

    request = next((r for r in requests if r["id"] == request_id), None)
    if request is None:
        return f"Ошибка: заявка №{request_id} не найдена"

    request["status"] = new_status
    request["history"].append(new_status)
    return f"Заявка №{request_id} переведена в статус '{new_status}'"


# 4. Ведение справочника материалов
def add_material(name, unit, stock):
    new_id = max((m["id"] for m in materials), default=0) + 1
    materials.append({"id": new_id, "name": name, "unit": unit, "stock": stock})
    return f"Материал '{name}' добавлен (id={new_id})"


def show_materials():
    lines = []
    for m in materials:
        lines.append(f"id={m['id']} | {m['name']} ({m['unit']}) | Остаток: {m['stock']}")
    return "\n".join(lines)


# 5. Просмотр истории статусов заявки
def show_history(request_id):
    request = next((r for r in requests if r["id"] == request_id), None)
    if request is None:
        return f"Ошибка: заявка №{request_id} не найдена"
    return f"История заявки №{request_id}: " + " → ".join(request["history"])


# ===== Демонстрация работы =====
print("=== Справочник материалов ===")
print(show_materials())

print("\n=== Создание заявок ===")
print(create_request("Иванов И.И.", 1, 5))
print(create_request("Петрова А.С.", 3, 2))

print("\n=== Все заявки ===")
print(show_requests())

print("\n=== Изменение статуса ===")
print(change_status(1, "На согласовании"))
print(change_status(1, "Утверждена"))

print("\n=== Заявки со статусом 'Новая' ===")
print(show_requests("Новая"))

print("\n=== История заявки №1 ===")
print(show_history(1))

print("\n=== Добавление нового материала ===")
print(add_material("Степлер", "шт", 15))