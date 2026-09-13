# Архітектура Diamant ID

## Поточна система

```text
Frontend (Pug + SCSS + JS, Gulp, :3000)
            │ HTTP / JSON + Bearer JWT
            ▼
Backend (FastAPI, SQLAlchemy, :8000)
            │
            ▼
MariaDB / XAMPP
├── diamond_oltp     експерти та звіти
├── diamond_market   довідники оцінок і ціновий індекс
└── diamond_analytics запланований аналітичний шар
```

`backend/main.py` містить HTTP-маршрути та dependencies; `crud.py` — доступ до даних; `models.py` — SQLAlchemy-моделі; `schemas.py` — API-контракти; `calculator.py` — правила IDC; `ml_service.py` — поточний демонстраційний прогноз ціни. Фронтенд компілюється з `frontend/src` у `frontend/dist` і не має власного серверного рендерингу.

## Середовища й гілки

Локальна розробка орієнтована на MariaDB/XAMPP і гілку `local-dev`. `main` буде гілкою deploy-кандидата після появи перевіреного PostgreSQL-контуру. Код не повинен розгалужуватися за гілкою: різниця середовищ належить до змінних середовища, драйвера БД і версіонованих міграцій.

Міграція до PostgreSQL виконується лише окремим етапом: конфігурація `DATABASE_URL`, Alembic, тестовий seed/дамп, перевірка цілісності, deployment та rollback-план. До цього MariaDB лишається єдиною підтримуваною runtime-БД.
