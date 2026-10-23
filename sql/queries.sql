-- ПР7: именованные запросы. Параметры :name передаются отдельно от SQL.
-- Набор используется непосредственно db/queries.py и веб-представлениями.

-- name: materials_list
-- 1. SELECT списка материалов, сортировка по названию.
SELECT id, name, unit, stock FROM materials ORDER BY name, id;

-- name: employees_list
-- 2. SELECT справочника сотрудников с сортировкой по подразделению.
SELECT id, name, email, department FROM employees ORDER BY department, name, id;

-- name: materials_available
-- 3. WHERE: материалы, которых достаточно для заданного количества.
SELECT id, name, unit, stock FROM materials
WHERE stock >= :quantity ORDER BY stock, name, id;

-- name: material_detail
-- 4. WHERE: конкретный материал по первичному ключу.
SELECT id, name, unit, stock FROM materials WHERE id = :id;

-- name: requests_all
-- 5. JOIN трёх таблиц: заявки, сотрудники и материалы.
SELECT r.*, m.name AS material_name, m.unit, e.name AS employee_name,
       e.department, e.email, strftime('%d.%m.%Y', r.created) AS created_display,
       (r.status = 'Отменена') AS is_cancelled
FROM supply_requests AS r
JOIN materials AS m ON m.id = r.material_id
JOIN employees AS e ON e.id = r.employee_id
ORDER BY r.created DESC, r.id DESC;

-- name: requests_active
-- 6. JOIN + WHERE: незавершённые заявки, конечные статусы исключены.
SELECT r.*, m.name AS material_name, m.unit, e.name AS employee_name,
       strftime('%d.%m.%Y', r.created) AS created_display,
       (r.status = 'Отменена') AS is_cancelled
FROM supply_requests AS r
JOIN materials AS m ON m.id = r.material_id
JOIN employees AS e ON e.id = r.employee_id
WHERE r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
ORDER BY r.created, r.id;

-- name: requests_on_date
-- 7. Параметризованный поиск заявок, созданных в выбранную дату.
SELECT r.*, m.name AS material_name, m.unit, e.name AS employee_name,
       strftime('%d.%m.%Y', r.created) AS created_display,
       (r.status = 'Отменена') AS is_cancelled
FROM supply_requests AS r
JOIN materials AS m ON m.id = r.material_id
JOIN employees AS e ON e.id = r.employee_id
WHERE r.created = :created ORDER BY r.id;

-- name: request_detail
-- 8. JOIN + WHERE: вся информация одной заявки, включая сотрудника.
SELECT r.*, m.name AS material_name, m.unit, m.stock,
       e.name AS employee_name, e.department, e.email,
       strftime('%d.%m.%Y', r.created) AS created_display,
       (r.status = 'Отменена') AS is_cancelled
FROM supply_requests AS r
JOIN materials AS m ON m.id = r.material_id
JOIN employees AS e ON e.id = r.employee_id WHERE r.id = :id;

-- name: request_history
-- 9. История статусов в исходном порядке, включая повторные статусы.
SELECT position, status FROM request_history
WHERE request_id = :id ORDER BY position;

-- name: material_summary
-- 10. Агрегаты COUNT: всего позиций и позиций в наличии.
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN stock > 0 THEN 1 END) AS in_stock
FROM materials;

-- name: request_summary
-- 11. Агрегаты COUNT: всего, активных и завершённых заявок.
SELECT COUNT(*) AS total,
       COUNT(CASE WHEN status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
                  THEN 1 END) AS active,
       COUNT(CASE WHEN status = 'Выполнена' THEN 1 END) AS completed
FROM supply_requests;

-- name: material_statistics
-- 12. LEFT JOIN + GROUP BY: спрос, включая материалы без активных заявок.
SELECT m.id, m.name, m.unit, m.stock, COUNT(r.id) AS requests_count,
       COALESCE(SUM(r.quantity), 0) AS requested_quantity
FROM materials AS m
LEFT JOIN supply_requests AS r ON r.material_id = m.id
    AND r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
GROUP BY m.id, m.name, m.unit, m.stock
ORDER BY requests_count DESC, m.id;

-- name: employee_statistics
-- 13. LEFT JOIN + GROUP BY: активные заявки по сотрудникам, включая нули.
SELECT e.id, e.name, e.department, COUNT(r.id) AS requests_count
FROM employees AS e
LEFT JOIN supply_requests AS r ON r.employee_id = e.id
    AND r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
GROUP BY e.id, e.name, e.department ORDER BY requests_count DESC, e.id;

-- name: popular_materials
-- 14. HAVING: материалы с количеством активных заявок больше порога.
SELECT m.id, m.name, COUNT(r.id) AS requests_count
FROM materials AS m
JOIN supply_requests AS r ON r.material_id = m.id
WHERE r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
GROUP BY m.id, m.name HAVING COUNT(r.id) > :minimum
ORDER BY requests_count DESC, m.id;

-- name: department_statistics
-- 15. GROUP BY + HAVING: подразделения с активными заявками больше порога.
SELECT e.department, COUNT(r.id) AS requests_count
FROM employees AS e
LEFT JOIN supply_requests AS r ON r.employee_id = e.id
    AND r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
GROUP BY e.department HAVING COUNT(r.id) > :minimum
ORDER BY requests_count DESC, e.department;

-- name: recent_requests
-- 16. Сортировка, LIMIT и OFFSET: последние заявки для обзора.
SELECT r.id, r.status, r.created, e.name AS employee_name,
       m.name AS material_name
FROM supply_requests AS r
JOIN employees AS e ON e.id = r.employee_id
JOIN materials AS m ON m.id = r.material_id
ORDER BY r.created DESC, r.id DESC LIMIT :limit OFFSET :offset;

-- name: materials_without_active
-- 17. Подзапрос NOT EXISTS: материалы без активных заявок.
SELECT m.id, m.name, m.unit, m.stock FROM materials AS m
WHERE NOT EXISTS (
    SELECT 1 FROM supply_requests AS r
    WHERE r.material_id = m.id
      AND r.status NOT IN ('Выполнена', 'Отклонена', 'Отменена')
)
ORDER BY m.name, m.id;
