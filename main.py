"""Консольный интерфейс сервиса заказа расходных материалов."""

from pathlib import Path

from materials import (
    add_material,
    check_stock,
    delete_material,
    find_material,
    sort_materials,
    update_material,
)
from orders import (
    VALID_STATUSES,
    cancel_request,
    change_status,
    create_request,
    filter_requests,
    show_history,
    show_requests,
)
from storage import (
    load_materials,
    load_requests,
    save_materials,
    save_requests,
)
from utils import input_int


DATA_DIR = Path(__file__).parent / "data"
MATERIALS_FILE = DATA_DIR / "materials.json"
REQUESTS_FILE = DATA_DIR / "requests.json"


def show_materials(materials: list[dict]) -> str:
    """Сформировать текстовую таблицу материалов."""
    if not materials:
        return "Материалы не найдены"

    lines = []
    for material in materials:
        lines.append(
            f"id={material['id']} | {material['name']} "
            f"({material['unit']}) | Остаток: {material['stock']}"
        )
    return "\n".join(lines)


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
        "7. Создать заявку\n"
        "8. Показать и отфильтровать заявки\n"
        "9. Изменить статус заявки\n"
        "10. Отменить заявку\n"
        "11. Показать историю заявки\n"
        "12. Показать материалы по возрастанию остатка\n"
        "0. Выход"
    )


def handle_choice(
    choice: int,
    materials: list[dict],
    requests: list[dict],
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
        print(f"Материал '{material['name']}' добавлен")
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
        print(f"Материал '{material['name']}' изменён")
    elif choice == 5:
        material_id = input_int("ID материала: ", minimum=1)
        material = delete_material(materials, material_id)
        save_materials(MATERIALS_FILE, materials)
        print(f"Материал '{material['name']}' удалён")
    elif choice == 6:
        material_id = input_int("ID материала: ", minimum=1)
        quantity = input_int("Требуемое количество: ", minimum=1)
        available = check_stock(materials, material_id, quantity)
        message = "достаточно" if available else "недостаточно"
        print(f"Материала на складе {message}")
    elif choice == 7:
        employee = input("Сотрудник: ").strip()
        material_id = input_int("ID материала: ", minimum=1)
        quantity = input_int("Количество: ", minimum=1)
        request = create_request(
            requests, materials, employee, material_id, quantity
        )
        save_requests(REQUESTS_FILE, requests)
        print(f"Заявка №{request['id']} создана")
    elif choice == 8:
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
    elif choice == 9:
        request_id = input_int("Номер заявки: ", minimum=1)
        print("Допустимые статусы: " + ", ".join(VALID_STATUSES))
        status = input("Новый статус: ").strip()
        request = change_status(requests, request_id, status)
        save_requests(REQUESTS_FILE, requests)
        print(f"Статус заявки №{request['id']} изменён")
    elif choice == 10:
        request_id = input_int("Номер заявки: ", minimum=1)
        request = cancel_request(requests, request_id)
        save_requests(REQUESTS_FILE, requests)
        print(f"Заявка №{request['id']} отменена")
    elif choice == 11:
        request_id = input_int("Номер заявки: ", minimum=1)
        print(show_history(requests, request_id))
    elif choice == 12:
        print(show_materials(sort_materials(materials, by="stock")))
    else:
        print("Неизвестный пункт меню")
    return True


def main() -> None:
    """Загрузить данные и запустить цикл консольного меню."""
    try:
        materials = load_materials(MATERIALS_FILE)
        requests = load_requests(REQUESTS_FILE)
    except (OSError, ValueError) as error:
        print(f"Не удалось загрузить данные: {error}")
        return

    while True:
        print_menu()
        choice = input_int("Выберите действие: ", minimum=0)
        try:
            if not handle_choice(choice, materials, requests):
                print("Данные сохранены. Работа завершена.")
                break
        except ValueError as error:
            print(f"Ошибка: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")


if __name__ == "__main__":
    main()
