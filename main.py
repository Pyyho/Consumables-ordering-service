"""Консольный интерфейс сервиса на объектной модели ПР3."""

from pathlib import Path

from models import Employee, Material, SupplyRequest
from models.materials import (
    add_material,
    check_stock,
    delete_material,
    find_material,
    get_material,
    show_materials,
    sort_materials,
    update_material,
)
from models.requests import (
    VALID_STATUSES,
    cancel_request,
    change_status,
    create_request,
    filter_requests,
    show_history,
    show_requests,
)
from models.users import (
    add_employee,
    find_employee,
    get_employee,
    show_employees,
)
from storage import (
    load_employees,
    load_materials,
    load_requests,
    save_employees,
    save_materials,
    save_requests,
)
from utils import input_int


DATA_DIR = Path(__file__).parent / "data"
MATERIALS_FILE = DATA_DIR / "materials.json"
EMPLOYEES_FILE = DATA_DIR / "employees.json"
REQUESTS_FILE = DATA_DIR / "requests.json"


def print_menu() -> None:
    """Вывести главное меню приложения."""
    print(
        "\n=== Сервис заказа расходных материалов ===\n"
        "1. Показать материалы\n"
        "2. Найти материал\n"
        "3. Добавить материал\n"
        "4. Изменить материал\n"
        "5. Удалить материал\n"
        "6. Проверить остаток\n"
        "7. Показать сотрудников\n"
        "8. Добавить сотрудника\n"
        "9. Найти сотрудника\n"
        "10. Создать заявку\n"
        "11. Показать и отфильтровать заявки\n"
        "12. Изменить статус заявки\n"
        "13. Отменить заявку\n"
        "14. Показать историю заявки\n"
        "15. Показать материалы по возрастанию остатка\n"
        "0. Выход"
    )


def save_all(
    materials: list[Material],
    employees: list[Employee],
    requests: list[SupplyRequest],
) -> None:
    """Сохранить все коллекции объектов в JSON-файлы."""
    save_materials(MATERIALS_FILE, materials)
    save_employees(EMPLOYEES_FILE, employees)
    save_requests(REQUESTS_FILE, requests)


def handle_choice(
    choice: int,
    materials: list[Material],
    employees: list[Employee],
    requests: list[SupplyRequest],
) -> bool:
    """Выполнить выбранное действие; вернуть False для выхода."""
    if choice == 0:
        return False

    if choice == 1:
        print(show_materials(materials))
    elif choice == 2:
        query = input("Часть названия: ").strip()
        print(show_materials(find_material(materials, query)))
    elif choice == 3:
        name = input("Название: ").strip()
        unit = input("Единица измерения: ").strip()
        stock = input_int("Остаток: ", minimum=0)
        material = add_material(materials, name, unit, stock)
        save_materials(MATERIALS_FILE, materials)
        print(f"Материал '{material.name}' добавлен")
    elif choice == 4:
        material_id = input_int("ID материала: ", minimum=1)
        name = input("Новое название (Enter — не менять): ").strip()
        unit = input("Новая единица (Enter — не менять): ").strip()
        stock_text = input("Новый остаток (Enter — не менять): ").strip()
        stock = int(stock_text) if stock_text else None
        material = update_material(
            materials,
            material_id,
            name=name or None,
            unit=unit or None,
            stock=stock,
        )
        save_materials(MATERIALS_FILE, materials)
        print(f"Материал '{material.name}' изменён")
    elif choice == 5:
        material_id = input_int("ID материала: ", minimum=1)
        if any(
            request.material.id == material_id for request in requests
        ):
            raise ValueError("материал используется в заявках и не удалён")
        material = delete_material(materials, material_id)
        save_materials(MATERIALS_FILE, materials)
        print(f"Материал '{material.name}' удалён")
    elif choice == 6:
        material_id = input_int("ID материала: ", minimum=1)
        quantity = input_int("Требуемое количество: ", minimum=1)
        message = (
            "достаточно"
            if check_stock(materials, material_id, quantity)
            else "недостаточно"
        )
        print(f"Материала на складе {message}")
    elif choice == 7:
        print(show_employees(employees))
    elif choice == 8:
        name = input("ФИО сотрудника: ").strip()
        email = input("Электронная почта: ").strip()
        department = input("Подразделение: ").strip()
        employee = add_employee(employees, name, email, department)
        save_employees(EMPLOYEES_FILE, employees)
        print(f"Сотрудник '{employee.name}' добавлен")
    elif choice == 9:
        query = input("Имя, почта или подразделение: ").strip()
        print(show_employees(find_employee(employees, query)))
    elif choice == 10:
        employee_id = input_int("ID сотрудника: ", minimum=1)
        material_id = input_int("ID материала: ", minimum=1)
        quantity = input_int("Количество: ", minimum=1)
        employee = get_employee(employees, employee_id)
        material = get_material(materials, material_id)
        if employee is None:
            raise ValueError(f"сотрудник с id={employee_id} не найден")
        if material is None:
            raise ValueError(f"материал с id={material_id} не найден")
        request = create_request(
            requests, employee, material, quantity
        )
        save_requests(REQUESTS_FILE, requests)
        print(f"Заявка №{request.id} создана")
    elif choice == 11:
        status = input("Статус (Enter — все): ").strip() or None
        employee = input("Сотрудник (Enter — все): ").strip() or None
        created = input("Дата ГГГГ-ММ-ДД (Enter — все): ").strip() or None
        selected = filter_requests(
            requests,
            status=status,
            employee=employee,
            created=created,
        )
        print(show_requests(selected))
    elif choice == 12:
        request_id = input_int("Номер заявки: ", minimum=1)
        print("Допустимые статусы: " + ", ".join(VALID_STATUSES))
        status = input("Новый статус: ").strip()
        request = change_status(requests, request_id, status)
        save_requests(REQUESTS_FILE, requests)
        print(f"Статус заявки №{request.id} изменён")
    elif choice == 13:
        request_id = input_int("Номер заявки: ", minimum=1)
        request = cancel_request(requests, request_id)
        save_requests(REQUESTS_FILE, requests)
        print(f"Заявка №{request.id} отменена")
    elif choice == 14:
        request_id = input_int("Номер заявки: ", minimum=1)
        print(show_history(requests, request_id))
    elif choice == 15:
        print(show_materials(sort_materials(materials, by="stock")))
    else:
        print("Неизвестный пункт меню")
    return True


def main() -> None:
    """Загрузить объекты и запустить цикл консольного меню."""
    try:
        materials = load_materials(MATERIALS_FILE)
        employees = load_employees(EMPLOYEES_FILE)
        requests = load_requests(REQUESTS_FILE, materials, employees)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"Не удалось загрузить данные: {error}")
        return

    while True:
        print_menu()
        choice = input_int("Выберите действие: ", minimum=0)
        try:
            if not handle_choice(choice, materials, employees, requests):
                save_all(materials, employees, requests)
                print("Данные сохранены. Работа завершена.")
                break
        except (OSError, ValueError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
