# План виконання робіт: Diamant ID

Цей план створено під час відновлення проєкту після захисту диплома.

## Статус на 2026-09-14

### Результат api-and-mvp-audit

Повний доказовий звіт: [api-mvp-audit.md](./api-mvp-audit.md). Безпечний API-аудит на свіжому FastAPI-процесі пройшов 10/10; на вже відкритому `:8000` читальні DB-маршрути зависли, тому перед наступною задачею потрібно перезапустити локальний backend і повторити `npm run audit:api`.

| API-група | Рішення |
| --- | --- |
| `/`, `/token` | Залишити; посилити auth/configuration. |
| `/users/*` | Залишити; обмежити ролі й створити admin/profile UI пізніше. |
| `/experts/` | Залишити: авторизований список не-admin експертів працює. |
| `GET /diamonds/*` | Залишити: dashboard-контракт містить `shape` і `cut_grade`; створити detail/passport UI. |
| `POST/PUT/DELETE /diamonds/*` | Залишити: час записується в секундах, update має owner/admin RBAC, update/delete повертають 404; далі create/edit UI. |
| `/market/*` | Залишити; прибрати frontend hardcode mappings/ціни та додати admin UI пізніше. |
| `/statistics/expert-performance` | Залишити після рішення про публічність usernames; додати analytics UI пізніше. |

Повних дублікатів endpoint-ів не знайдено. Невикористаний CRUD-дублікат `crud.get_diamonds()` вилучено. Окремо лишаються дубльовані frontend API origin/mappings/формула ціни. `scripts/seed_db-start.py` вилучено, а `diamond_analytics.ml_results` формалізовано як зарезервовану SQLAlchemy-модель.

### Уже реалізовано

- [x] FastAPI backend із JWT-входом, RBAC для admin/gemologist, CRUD звітів і довідниками ринку.
- [x] SQLAlchemy-моделі для OLTP та Market; локальний seed для MariaDB.
- [x] IDC-калькулятор proportions/cut і демонстраційний ML-розрахунок ціни.
- [x] Gulp-збірка Pug/SCSS/JavaScript; сторінки landing, login, dashboard і створення звіту.
- [x] Збірка frontend і імпорт FastAPI проходять у поточному середовищі.

### Пріоритет 1 — стабільний локальний MVP

- [x] Зафіксувати безпечну конфігурацію: `.env.example`, обов’язковий `SECRET_KEY`, явний `DATABASE_URL` або `DB_*`, без production-дефолтів.
- [x] Прибрати перевірку паролів у відкритому вигляді; seed-користувачі хешуються bcrypt.
- [x] Усунути розходження актуального `seed_db.py`, legacy `seed_db-start.py` і моделей: seed відтворює всі три схеми, а `ml_results` формалізовано моделлю.
- [x] Виконати clean seed MariaDB та API smoke-flow: bcrypt-login admin і першого експерта, `npm run audit:api` — 10/10.
- [x] Виправити `/experts/`, `POST/PUT/DELETE /diamonds/*`, 404-відповіді та owner/admin RBAC; синхронізувати API response models із dashboard.
- [ ] Завершити інтеграцію frontend ↔ API: єдиний API-клієнт, server mappings/price, dashboard, створення, detail/passport і редагування звітів.
- [x] Визначити долю `diamond_analytics.ml_results`: зберігаємо таблицю як зарезервований аналітичний шар, описуємо моделлю та відтворюємо порожньою через локальний seed; API/ML — окрема задача.

### Пріоритет 2 — якість і тестування

- [ ] Додати `pytest`, `pytest-cov`, конфігурацію та маркери `unit`, `api`, `integration`.
- [ ] Unit-тести IDC-калькулятора: межі діапазонів, найгірша оцінка, некоректні значення.
- [ ] Unit-тести ML-сервісу з контрольованою випадковістю.
- [ ] API-тести auth, RBAC, CRUD, 404/422 та помилок валідації з ізольованою БД.
- [ ] Frontend DOM/smoke та browser E2E: login → dashboard → створення → detail/edit звіту після виправлення контрактів.

### Пріоритет 3 — PostgreSQL і тестовий домен

- [ ] Відокремити конфігурацію БД від MariaDB-специфічного коду, зберігши локальну MariaDB.
- [ ] Ввести версіоновані міграції (Alembic), базовий seed/backfill і rollback-процедуру.
- [ ] Перевірити PostgreSQL-діалект, перенести тестові дані та звірити кількість/цілісність записів.
- [ ] Підготувати Dockerfile й deployment-конфігурацію для обраного backend-провайдера; frontend — для shared hosting.
- [ ] Налаштувати CORS, env secrets, health-check, домени/TLS та ручний smoke-test до публічного запуску.

### Зафіксовані розбіжності з початковими нотатками

- Нотатки описують локальний backend у Docker, але поточний репозиторій запускає FastAPI напряму з `.venv`; Docker ще не реалізований.
- Фактична MariaDB уже містить `diamond_analytics.ml_results`, але SQLAlchemy-моделі, актуальний seed і робочий ML-потік для неї відсутні.
- Документований публічний паспорт, QR, сторінки `view-report`, admin і ML-аналітика ще не присутні як завершений код у репозиторії.

### Рішення щодо гілок

- `local-dev`: базова гілка локальної розробки з MariaDB.
- `main`: майбутній deploy-кандидат для PostgreSQL; merge лише після локальних перевірок і окремого плану розгортання.
- Робота ведеться в короткоживучих task-гілках від `local-dev`; гілка `agent-project-foundation` — перехідна для цього налаштування.

---
