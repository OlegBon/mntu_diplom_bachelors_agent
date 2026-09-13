# Локальний запуск Diamant ID

## Передумови

- Python 3.13 і віртуальне середовище `.venv`.
- Node.js та залежності в `frontend/node_modules`.
- Запущений MySQL/MariaDB у XAMPP на параметрах із приватного `.env`. Apache для поточного FastAPI/Gulp запуску не потрібен.
- Поточна перевірена конфігурація: Python 3.13.7, Node.js 24.18.0, npm 12.0.1, MariaDB 10.4.32.

## Backend

Команди нижче запускай з кореня репозиторію. Якщо термінал уже відкрито в папці `backend`, спершу виконай `cd ..`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Після запуску API доступний за `http://127.0.0.1:8000`, Swagger — за `/docs`. Не публікуй `.env` і не копіюй його значення в документацію.

Для швидкої перевірки після запуску відкрий `http://127.0.0.1:8000/`; очікувана відповідь містить повідомлення про роботу Diamond Identification System API.

### Якщо проєкт було перенесено або клоновано

`.venv` не можна переносити між папками: Windows-запускачі пакетів зберігають абсолютний шлях до Python. Якщо бачиш `Fatal error in launcher`, відтвори лише віртуальне середовище з кореня репозиторію:

```powershell
deactivate  # якщо середовище активне
Remove-Item .venv -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Це не змінює вихідний код, `.env` або дані MariaDB. Рекомендований спосіб запуску після активації — `python -m uvicorn ...`, а не прямий виклик `uvicorn ...`.

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

Gulp/Browsersync зазвичай віддає збірку на `http://localhost:3000`; якщо порт зайнятий, він обере інший локальний порт. API дозволяє CORS-запити лише з `localhost` або `127.0.0.1` з номером порту, тому зміна локального порту не блокує вхід. `frontend/dist` генерується автоматично.

Перший старт BrowserSync може завершитися через кілька секунд після завершення Gulp-збірки. Зупиняй backend або frontend через `Ctrl+C` у відповідному терміналі.
