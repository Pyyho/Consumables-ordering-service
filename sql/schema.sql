-- Реляционная модель сервиса заказа расходных материалов (ПР7).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    unit TEXT NOT NULL CHECK (length(trim(unit)) > 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    department TEXT NOT NULL CHECK (length(trim(department)) > 0)
);

CREATE TABLE IF NOT EXISTS supply_requests (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    created TEXT NOT NULL CHECK (created GLOB '????-??-??'),
    status TEXT NOT NULL DEFAULT 'Новая' CHECK (status IN (
        'Новая', 'На согласовании', 'Утверждена', 'В закупке',
        'Выполнена', 'Отклонена', 'Отменена'
    ))
);

CREATE TABLE IF NOT EXISTS request_history (
    request_id INTEGER NOT NULL REFERENCES supply_requests(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 0),
    status TEXT NOT NULL CHECK (status IN (
        'Новая', 'На согласовании', 'Утверждена', 'В закупке',
        'Выполнена', 'Отклонена', 'Отменена'
    )),
    PRIMARY KEY (request_id, position)
);

CREATE INDEX IF NOT EXISTS requests_material_idx ON supply_requests(material_id);
CREATE INDEX IF NOT EXISTS requests_employee_idx ON supply_requests(employee_id);
CREATE INDEX IF NOT EXISTS requests_created_idx ON supply_requests(created);
