# Локальні правила: база даних

## Поточне середовище

- Локальна runtime-БД — MariaDB/XAMPP з трьома physical databases: `diamond_oltp`, `diamond_market`, `diamond_analytics`. ORM завжди задає logical schema явно; `diamond_analytics.ml_results` існує як порожній reserved layer, а demo SOM artifacts належать `diamond_oltp`.
- Не розкривай рядок підключення, паролі або інші значення `.env`.

## Схема і доступ до даних

- Точно описуй primary keys, foreign keys, `NOT NULL`, unique indexes, індекси та поведінку зв'язків.
- Грошові значення зберігай через `DECIMAL`, не `float`. Фільтри, `JOIN` і сортування зіставляй з індексами.
- Не конкатенуй введення користувача в SQL; використовуй SQLAlchemy або параметризований SQL.

## Зміни даних

- `scripts/seed_db.py` руйнівно перестворює бази: не запускай його без підтвердження користувача.
- Нові зміни схеми не маскуй у `create_all`: спершу погодь версіоновані міграції, backfill і rollback.
- Майбутня PostgreSQL-міграція включає `DATABASE_URL`, Alembic, тестовий seed, звірку даних і rollback-план.
