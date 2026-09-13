# Правила бази даних

- Локальна MariaDB: `diamond_oltp`, `diamond_market`, `diamond_analytics`. Описуй primary keys, foreign keys, `NOT NULL`, unique indexes та індекси точно.
- `scripts/seed_db.py` руйнівно перестворює бази: не запускай його без підтвердження користувача.
- Нові зміни схеми не маскуй у `create_all`: спершу погодь версіоновані міграції й backfill.
- Майбутня PostgreSQL-міграція включає `DATABASE_URL`, Alembic, тестовий seed, звірку даних і rollback-план.
