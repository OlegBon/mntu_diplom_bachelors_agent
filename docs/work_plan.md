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
| `/diamonds/*` | Тимчасово зберегти як legacy compatibility API; чинні dashboard і wizard вже використовують `/reports`. Після 080 провести usage-аудит і погоджене прибирання в 085. |
| `/market/*` | Залишити; прибрати frontend hardcode mappings/ціни та додати admin UI пізніше. |
| `/statistics/expert-performance` | Залишити після рішення про публічність usernames; додати analytics UI пізніше. |

Повних дублікатів endpoint-ів не знайдено. Невикористаний CRUD-дублікат `crud.get_diamonds()` вилучено. Dashboard і wizard перенесені на `/reports`, але `frontend/src/js/main.js` ще містить unreachable legacy handler `/diamonds/*`; його безпечне вилучення заплановано після 080. `scripts/seed_db-start.py` вилучено, а `diamond_analytics.ml_results` формалізовано як зарезервовану SQLAlchemy-модель.

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
- [ ] Завершити інтеграцію frontend ↔ API: єдиний API-клієнт, server mappings/price, dashboard, створення, private detail/edit і public passport.
- [x] Визначити долю `diamond_analytics.ml_results`: зберігаємо таблицю як зарезервований аналітичний шар, описуємо моделлю та відтворюємо порожньою через локальний seed; API/ML — окрема задача.

### Пріоритет 2 — якість і тестування

- [x] Додати `pytest`, `pytest-cov`, конфігурацію та маркери `unit`, `api`, `integration`.
- [x] Додати базові unit-тести IDC-калькулятора: межі діапазонів і найгірша оцінка; некоректні доменні значення потребують окремо погоджених правил валідації.
- [x] Додати unit-тест ML-сервісу з контрольованими market price та випадковістю.
- [x] Додати API/integration-тести auth, RBAC, створення/видалення звітів, 404/422 та ізольовану SQLite БД.
- [x] Додати frontend JS-модульні тести, jsdom DOM smoke та базовий Playwright browser smoke login-сторінки.
- [ ] Розширити browser E2E: реальний login → dashboard → створення → detail/edit звіту після безпечної test-auth стратегії; поточні Playwright flows використовують mock HTTP.
- [ ] Окремо усунути попередження SQLAlchemy 2 (`declarative_base`) і Pydantic 2 (`class Config`, `.dict()`), підтвердивши сумісність API-тестами.

### Пріоритет 3 — завершення локального MVP

Детальна активна декомпозиція ведеться у [docs/backlog](./backlog/README.md).
Ціль етапу — завершити локальний workflow експертного звіту до переходу до
перевіреного ML та PostgreSQL/deployment.

- [x] [010 — Контракт предметної області звіту](./decisions/001-report-domain-contract.md): камінь, звіт, продаж, медіа, паспорт, RBAC, API-контракти та план backfill.
- [x] [015 — Guide поточного доменного workflow](./guides/current-domain-and-report-workflow.md): фактична логіка ролей, звіту, ціни, dashboard, файлів і меж MVP відокремлена від запланованого контракту.
- [x] 020 — Основа версіонованих міграцій: Alembic `0001_initial_schema`, безпечний bootstrap databases, migration-aware seed і перевірений MariaDB rollback; команди — у [local-start.md](./local-start.md).
- [x] 030 — UX і візуальна основа: погоджені right-aligned desktop menu, сапфірова дизайн-система, responsive shell, public landing і правила інтерфейсних станів — [product-ux-foundation.md](./guides/product-ux-foundation.md).
- [x] 035 — RBAC створення звіту: `POST /diamonds/` дозволений лише ролі `gemologist`; для admin повертається `403`, а обидва сценарії покриті API/integration-тестами. Frontend не показує admin пункт «Новий звіт» ані в header, ані на dashboard; `/dashboard.html` і `/create-report.html` вимагають локальної сесії, а прямий перехід admin на форму повертає до списку звітів.
- [x] [037 — Фінансовий контракт](./decisions/002-financial-calculation-contract.md): поточний `price` визначено як legacy-значення, `6000` — технічний demo-індекс без валюти й одиниці; для локальної dashboard-вітрини погоджено окреме `USD … d` позначення demo-набору 2023–2025 без переоцінки історичних записів.
- [x] [040 — Ядро звіту й довідники](./decisions/003-report-core-migration-plan.md): `Stone`, lifecycle `draft → review → issued → void`, audit events, серверні довідники, приватний `/reports` API й Alembic `0002_report_core` застосовані до локальної MariaDB; 1 000 legacy-записів збережено як draft без фінансової перекласифікації.
- [x] 050 — Медіа звітів: `MediaAsset`, gitignored private storage, signature/type/size checks, owner/admin RBAC та локальні placeholders. Legacy image-path рядки не вважаються вкладеннями й не переносилися; public media лишається частиною 090.
- [x] 055 — UI-примітиви: канонічні SCSS controls, flat large surfaces, 2px compact controls, спільні nav/footer/session-actions, text-only кнопки, filter/pagination стилі й DOM-перевірка. Наступні UI-зрізи мають використовувати `_ui-primitives.scss`.
- [x] 060 — Dashboard звітів: приватний `/reports`, server-driven список, пошук, швидкі статуси звіту та двостанова проєкція продажу «Продано / Не продано», розширені фільтри 4C/форми/діапазонів/дат, RBAC, URL-параметри, пагінація, клікабельні server-side сортування, вітрина з 4C/бейджами й demo-ціною `USD … d`, а також меню дій `⋮`; приватний detail/edit/print залишаються 080.
- [x] 070 — Майстер створення звіту: три кроки, серверні довідники, `examination_date`, preview наступного ID, live IDC preview, детермінований demo-прогноз `USD … d`, валідація, приватні вкладення та підтверджене ручне збереження `draft`. Detail/edit, commercial state і transitions лишаються 080.
- [x] 080 — Приватний перегляд і редагування: `/report-detail.html`, private owner/admin RBAC, draft-редагування повного контракту, детальний `market_status`, вкладення, history та lifecycle actions. Кожний успішний `PUT /reports/{id}` додає `report_updated`; `issued` доступний admin лише за видимих expert-confirmed grades. Друк не входив у цей зріз.
- [ ] [085 — Прибирання legacy API](./backlog/085-legacy-api-retirement.md): після 080 прибрати unreachable frontend handler `/diamonds/*` та погоджено визначити долю compatibility маршрутів.
- [ ] [090 — Публічний паспорт і QR](./backlog/090-public-passport-and-qr.md): окремий безпечний public flow для `issued`.
- [ ] [100 — Профіль і admin UI](./backlog/100-profile-and-admin-ui.md): експерти, ролі та довідники; UI ринкових даних залежить від 110.
- [ ] [110 — Авторитетні ринкові дані й валютні курси](./backlog/110-authoritative-market-data-and-fx.md): обрати законне джерело, зберігати незмінні snapshot-и з provenance, реалізувати ручне admin-оновлення, а scheduler розглядати лише після цього. Не змінює demo `USD … d` або історичні значення автоматично.

### Пріоритет 4 — перевірений ML, PostgreSQL і тестовий домен

- [x] **mariadb-local-recovery:** локальний MariaDB відновлено в поточному
  XAMPP через чистий `mysql/data` та перевірені SQL-дампи. Відновлено три
  бази Diamant ID і три інші користувацькі бази; старий data-directory
  збережено окремим архівом. Runbook:
  [mariadb-local-recovery.md](./guides/mariadb-local-recovery.md).
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
