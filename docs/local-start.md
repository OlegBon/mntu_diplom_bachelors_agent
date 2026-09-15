# Локальний запуск Diamant ID

## Передумови

- Python 3.13 і віртуальне середовище `.venv`.
- Node.js та залежності в `frontend/node_modules`.
- Запущений MySQL/MariaDB у XAMPP на параметрах із приватного `.env`. Apache для поточного FastAPI/Gulp запуску не потрібен.
- Поточна перевірена конфігурація: Python 3.13.7, Node.js 24.18.0, npm 12.0.1, MariaDB 10.4.32.

## Конфігурація `.env`

Скопіюй `.env.example` у приватний `.env` та задай усі значення безпечними локальними даними. Застосунок потребує непорожній `SECRET_KEY`; для БД можна вказати `DATABASE_URL` або окремі `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` і `DB_NAME`. Значення `.env` не комітуються й не потрапляють у документацію.

`SEED_ADMIN_PASSWORD` і `SEED_GEMOLOGIST_PASSWORD` застосовуються лише руйнівним `scripts/seed_db.py`: він записує в БД тільки bcrypt-хеші. Після першого переходу на цей seed старі облікові дані з наявної БД більше не підходять; виконай seed лише тоді, коли локальні дані можна втратити. `MEDIA_STORAGE_PATH` необов’язкова: без неї приватні файли лежать у gitignored `storage/reports`; для іншого локального диска задай абсолютний шлях у приватному `.env`.

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

### Alembic і локальна схема

Alembic є джерелом істини для структури таблиць. Три логічні схеми Diamant ID
у MariaDB є окремими databases, тому на **новому порожньому** локальному
середовищі спочатку потрібно створити лише відсутні databases, а потім
застосувати міграції:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_mariadb_databases.py
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```

`bootstrap_mariadb_databases.py` виконує тільки `CREATE DATABASE IF NOT EXISTS`
для `diamond_oltp`, `diamond_market` і `diamond_analytics`: наявні databases,
таблиці й дані він не видаляє. `upgrade head` змінює схему, тому перед ним
зроби резервну копію даних, якщо вони цінні.

Поточний репозиторій має revisions `0002_report_core`, `0003_media_assets` і
`0004_report_wizard`. Для наявної локальної БД,
що вже позначена `0001_initial_schema`, ця revision створює нормалізовані
`stones`, `report_events`, `stone_valuations`, `reference_values`, доповнює
`diamond_reports` lifecycle-полями й переносить legacy-звіти у draft. Перед
застосуванням звір generated SQL без зміни БД:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head --sql
```

Після резервної копії та окремого підтвердження застосуй revision, а потім
переконайся, що версія стала `0004_report_wizard`:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m alembic -c alembic.ini current
```

Не запускай `downgrade` для цієї БД: він вилучить нові нормалізовані таблиці й
колонки. Revision `0003_media_assets` створює лише metadata приватних
вкладень і не переносить legacy `plotting_image`/`real_image`. Для перевірки
Revision `0004_report_wizard` додає nullable `examination_date` для report та
довідники geometry, не змінюючи legacy-записи. Після upgrade перезапусти
backend; чинний `/diamonds/*` зберігає
сумісність, а create-form після створення звіту дозавантажує вибрані
JPEG/PNG/WebP-файли через захищений `/reports/{id}/media`.

Для наявної локальної БД без `alembic_version` спочатку перевір поточний стан:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini current
```

Якщо таблиці вже відповідають перевіреній стартовій схемі, її можна позначити
командою `stamp 0001_initial_schema`. Це записує версію в `alembic_version`,
тому виконуй stamp лише після резервної копії та окремого підтвердження.
**Лише після stamp** запускай `alembic check`: він порівнює ORM metadata з
MariaDB і має завершитися без нових upgrade-операцій. Не застосовуй `downgrade`
до БД із потрібними даними: початковий downgrade видаляє таблиці.

### Руйнiвний seed

`scripts/seed_db.py` видаляє та створює заново `diamond_oltp`, `diamond_market` і `diamond_analytics`, а таблиці після цього створює через `alembic upgrade head`. Перед запуском переконайся, що це локальна тестова MariaDB і дані можна втратити.

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

## Автоматизовані тести

Тести не використовують локальні дані XAMPP: backend набір створює SQLite у пам’яті, а frontend browser smoke підіймає тимчасовий BrowserSync.

```powershell
.\.venv\Scripts\python.exe -m pytest
cmd /c "cd frontend && npm test"
cmd /c "cd frontend && npm run test:e2e"
```

Перед першим browser E2E один раз встанови локальний браузер Playwright: `cmd /c "cd frontend && npx playwright install chromium chromium-headless-shell"`. Поточний E2E перевіряє лише відображення login-сторінки й не виконує вхід під реальним користувачем.
