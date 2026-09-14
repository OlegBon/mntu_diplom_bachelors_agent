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

- [x] Додати `pytest`, `pytest-cov`, конфігурацію та маркери `unit`, `api`, `integration`.
- [x] Додати базові unit-тести IDC-калькулятора: межі діапазонів і найгірша оцінка; некоректні доменні значення потребують окремо погоджених правил валідації.
- [x] Додати unit-тест ML-сервісу з контрольованими market price та випадковістю.
- [x] Додати API/integration-тести auth, RBAC, створення/видалення звітів, 404/422 та ізольовану SQLite БД.
- [x] Додати frontend JS-модульні тести, jsdom DOM smoke та базовий Playwright browser smoke login-сторінки.
- [ ] Розширити browser E2E: реальний login → dashboard → створення → detail/edit звіту після відповідних UI-зрізів і безпечної test-auth стратегії.
- [ ] Окремо усунути попередження SQLAlchemy 2 (`declarative_base`) і Pydantic 2 (`class Config`, `.dict()`), підтвердивши сумісність API-тестами.

### Пріоритет 3 — завершення локального MVP

Детальна активна декомпозиція ведеться у [docs/backlog](./backlog/README.md).
Ціль етапу — завершити локальний workflow експертного звіту до переходу до
перевіреного ML та PostgreSQL/deployment.

- [x] [010 — Контракт предметної області звіту](./decisions/001-report-domain-contract.md): камінь, звіт, продаж, медіа, паспорт, RBAC, API-контракти та план backfill.
- [x] [015 — Guide поточного доменного workflow](./guides/current-domain-and-report-workflow.md): фактична логіка ролей, звіту, ціни, dashboard, файлів і меж MVP відокремлена від запланованого контракту.
- [x] 020 — Основа версіонованих міграцій: Alembic `0001_initial_schema`, безпечний bootstrap databases, migration-aware seed і перевірений MariaDB rollback; команди — у [local-start.md](./local-start.md).
- [x] 030 — UX і візуальна основа: погоджені right-aligned desktop menu, сапфірова дизайн-система, responsive shell, public landing і правила інтерфейсних станів — [product-ux-foundation.md](./guides/product-ux-foundation.md).
- [ ] [035 — Server-side RBAC створення звіту](./backlog/035-admin-report-rbac.md): admin не створює первинні експертні звіти; потрібні `403` і тести для обох ролей.
- [ ] [037 — Фінансові розрахунки та контракт ціни](./backlog/037-financial-calculation-rules.md): розмежувати ринкову довідку, системний прогноз, експертну оцінку й факт продажу; визначити точність, валюту, джерело та округлення до зміни моделі звіту.
- [ ] [040 — Ядро звіту й довідники](./backlog/040-report-core-and-reference-data.md): стани, дані каменю, валідація й серверні mappings.
- [ ] [050 — Медіа звітів](./backlog/050-media-assets.md): upload, приватне storage і метадані.
- [ ] [055 — UI-примітиви](./backlog/055-ui-primitives.md): спільні Pug/SCSS-компоненти після ядра звіту, до dashboard і wizard; не залежить від медіа.
- [ ] [060 — Dashboard звітів](./backlog/060-reports-dashboard.md): фактичний список, фільтри, пошук і пагінація.
- [ ] [070 — Майстер створення звіту](./backlog/070-report-creation-wizard.md): draft, live preview, валідація та вкладення.
- [ ] [080 — Приватний перегляд і редагування](./backlog/080-report-detail-and-editing.md): RBAC, transitions, аудит подій.
- [ ] [090 — Публічний паспорт і QR](./backlog/090-public-passport-and-qr.md): окремий безпечний public flow для `issued`.
- [ ] [100 — Профіль і admin UI](./backlog/100-profile-and-admin-ui.md): експерти, ролі, довідники та ринкові дані.

### Пріоритет 4 — перевірений ML, PostgreSQL і тестовий домен

- [ ] Відокремити конфігурацію БД від MariaDB-специфічного коду, зберігши локальну MariaDB.
- [ ] Після локального MVP реалізувати перевірений ML-контур: датасет, versioned model artifact, валідація метрик, відтворюваний прогноз і окремі аналітичні результати.
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
