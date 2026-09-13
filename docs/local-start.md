# Локальний запуск Diamant ID

## Передумови

- Python 3.13 і віртуальне середовище `.venv`.
- Node.js та залежності в `frontend/node_modules`.
- Запущений MySQL/MariaDB у XAMPP на параметрах із приватного `.env`.

## Backend

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Після запуску API доступний за `http://127.0.0.1:8000`, Swagger — за `/docs`. Не публікуй `.env` і не копіюй його значення в документацію.

## Дані

`scripts/seed_db.py` видаляє та створює заново `diamond_oltp` і `diamond_market`. Перед запуском переконайся, що це локальна тестова MariaDB і дані можна втратити.

```powershell
.\.venv\Scripts\python.exe scripts\seed_db.py
```

## Frontend

```powershell
cmd /c "cd frontend && npm run build"
cmd /c "cd frontend && npm start"
```

Gulp/Browsersync віддає збірку на `http://localhost:3000`. `frontend/dist` генерується автоматично.
