# План виконання робіт: Diamant ID

Цей план створено під час відновлення проєкту після захисту диплома.

## Статус на 2026-09-14

### Результат api-and-mvp-audit

Повний доказовий звіт: [api-mvp-audit.md](./api-mvp-audit.md). Безпечний API-аудит на свіжому FastAPI-процесі пройшов 10/10; на вже відкритому `:8000` читальні DB-маршрути зависли, тому перед наступною задачею потрібно перезапустити локальний backend і повторити `npm run audit:api`.

| API-група | Рішення |
| --- | --- |
| `/`, `/token` | Залишити; посилити auth/configuration. |
| `/users/*` | Залишити; обмежити ролі й створити admin/profile UI пізніше. |
| `/experts/` | Виправити: маршрут не повертає зібраний список. |
| `GET /diamonds/*` | Залишити; синхронізувати response model із dashboard і створити detail/passport UI. |
| `POST/PUT/DELETE /diamonds/*` | Виправити: помилкове поле часу, owner/admin RBAC, 404; потім додати create/edit UI. |
| `/market/*` | Залишити; прибрати frontend hardcode mappings/ціни та додати admin UI пізніше. |
| `/statistics/expert-performance` | Залишити після рішення про публічність usernames; додати analytics UI пізніше. |

Повних дублікатів endpoint-ів не знайдено. Окремо прибрати або узгодити: невикористаний `crud.get_diamonds()`, старий `scripts/seed_db-start.py`, дубльовані frontend API origin/mappings/формулу ціни. Фактична БД містить неописаний у моделях `diamond_analytics.ml_results`; до міграції треба формально включити його в контур або окремо прибрати після рішення щодо даних.

### Уже реалізовано

- [x] FastAPI backend із JWT-входом, RBAC для admin/gemologist, CRUD звітів і довідниками ринку.
- [x] SQLAlchemy-моделі для OLTP та Market; локальний seed для MariaDB.
- [x] IDC-калькулятор proportions/cut і демонстраційний ML-розрахунок ціни.
- [x] Gulp-збірка Pug/SCSS/JavaScript; сторінки landing, login, dashboard і створення звіту.
- [x] Збірка frontend і імпорт FastAPI проходять у поточному середовищі.

### Пріоритет 1 — стабільний локальний MVP

- [ ] Зафіксувати безпечну конфігурацію: `.env.example`, обов’язковий `SECRET_KEY`, явний `DATABASE_URL`, без production-дефолтів.
- [ ] Прибрати перевірку паролів у відкритому вигляді; хешувати seed-користувачів bcrypt.
- [ ] Усунути розходження актуального `seed_db.py`, legacy `seed_db-start.py`, моделей і фактичної MariaDB; перевірити запуск із чистої локальної MariaDB.
- [ ] Виправити `/experts/`, `POST/PUT/DELETE /diamonds/*`, 404-відповіді та owner/admin RBAC; синхронізувати API response models із UI.
- [ ] Завершити інтеграцію frontend ↔ API: єдиний API-клієнт, server mappings/price, dashboard, створення, detail/passport і редагування звітів.
- [ ] Визначити долю `diamond_analytics.ml_results`: описати моделлю й міграцією або безпечно прибрати окремим погодженим кроком.

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
