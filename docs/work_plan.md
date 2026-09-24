# План виконання робіт: Diamant ID

Цей план створено під час відновлення проєкту після захисту диплома.

## Зведений статус на 2026-09-16

### Результат api-and-mvp-audit

Історичний доказовий звіт і його актуалізація: [api-mvp-audit.md](./api-mvp-audit.md). Безпечний API-аудит не змінює дані; поточний скрипт перевіряє 13 публічних/401/CORS контрактів після запуску локального backend. Старий інцидент зависання процесу `:8000` належить до стану до MariaDB recovery і не є актуальним висновком про код.

| API-група | Рішення |
| --- | --- |
| `/`, `/token` | Залишити; посилити auth/configuration. |
| `/users/*` | Залишити; обмежити ролі й створити admin/profile UI пізніше. |
| `/experts/` | Залишити: авторизований список не-admin експертів працює. |
| `/reports` | Єдиний private API звітів; legacy `/diamonds/*` вилучено в 085 без міграції historical даних. |
| `/market/*` | Compatibility mappings і технічний demo-індекс; не використовувати як authorative market data. Контрольовані provider snapshot-и належать `/market-data/*`. |
| `/statistics/expert-performance`, `/statistics/admin-review-performance` | Admin-only operational analytics: status counts за датою створення report, завершені server-timed active sessions та review-cycle за датою admin-рішення. |

Повних дублікатів endpoint-ів не лишилося. Dashboard, wizard і detail/edit працюють через `/reports`; legacy `/diamonds/*`, unreachable handler, demo `MLService` і небезпечний `scripts/recalc_grades.py` вилучено. Historical projection-колонки лишаються compatibility-даними без cleanup/backfill; `scripts/seed_db-start.py` вилучено, а `diamond_analytics.ml_results` формалізовано як порожню зарезервовану SQLAlchemy-модель.

### Уже реалізовано

- [x] FastAPI backend із JWT-входом, RBAC для admin/gemologist, CRUD звітів і довідниками ринку.
- [x] SQLAlchemy-моделі для OLTP та Market; локальний seed для MariaDB.
- [x] IDC-калькулятор proportions/cut із versioned ruleset; він не є ML, експертною сертифікацією або ринковою ціною.
- [x] Gulp-збірка Pug/SCSS/JavaScript; сторінки landing, login, dashboard і створення звіту.
- [x] Збірка frontend і імпорт FastAPI проходять у поточному середовищі.

### Пріоритет 1 — стабільний локальний MVP

- [x] Зафіксувати безпечну конфігурацію: `.env.example`, обов’язковий `SECRET_KEY`, явний `DATABASE_URL` або `DB_*`, без production-дефолтів.
- [x] Прибрати перевірку паролів у відкритому вигляді; seed-користувачі хешуються bcrypt.
- [x] Усунути розходження актуального `seed_db.py`, legacy `seed_db-start.py` і моделей: seed відтворює всі три схеми, а `ml_results` формалізовано моделлю.
- [x] Виконати clean seed MariaDB та API smoke-flow: bcrypt-login admin і першого експерта, `npm run audit:api` — 10/10.
- [x] Виправити `/experts/`, `POST/PUT/DELETE /diamonds/*`, 404-відповіді та owner/admin RBAC; синхронізувати API response models із dashboard.
- [x] Завершити інтеграцію frontend ↔ API: єдиний API-клієнт, server mappings/price, dashboard, створення, private detail/edit, profile/admin UI та public passport/PDF реалізовано; real browser E2E проходить у disposable SQLite runtime без доступу до MariaDB.
- [x] Визначити долю `diamond_analytics.ml_results`: зберігаємо таблицю як зарезервований аналітичний шар, описуємо моделлю та відтворюємо порожньою через локальний seed; API/ML — окрема задача.

### Пріоритет 2 — якість і тестування

- [x] Додати `pytest`, `pytest-cov`, конфігурацію та маркери `unit`, `api`, `integration`.
- [x] Додати базові unit-тести IDC-калькулятора: межі діапазонів і найгірша оцінка; некоректні доменні значення потребують окремо погоджених правил валідації.
- [x] Додати unit-тест ML-сервісу з контрольованими market price та випадковістю.
- [x] Додати API/integration-тести auth, RBAC, створення/видалення звітів, 404/422 та ізольовану SQLite БД.
- [x] Додати frontend JS-модульні тести, jsdom DOM smoke та базовий Playwright browser smoke login-сторінки.
- [x] Розширити browser E2E: реальний login → dashboard → створення → detail/edit → review → issued → passport/PDF виконується у disposable SQLite runtime з окремими test accounts і storage; mock contract приватного паспорта синхронізований із wrapper-відповіддю API.
- [ ] Окремо усунути попередження SQLAlchemy 2 (`declarative_base`) і Pydantic 2 (`class Config`, `.dict()`), підтвердивши сумісність API-тестами — [136](./backlog/136-sqlalchemy-pydantic-deprecation-cleanup.md).

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
- [x] 050 — Медіа звітів: `MediaAsset`, gitignored private storage, signature/type/size checks, owner/admin RBAC та локальні placeholders. Legacy image-path рядки не вважаються вкладеннями й не переносилися.
- [x] 055 — UI-примітиви: канонічні SCSS controls, flat large surfaces, 2px compact controls, спільні nav/footer/session-actions, text-only кнопки, filter/pagination стилі й DOM-перевірка. Наступні UI-зрізи мають використовувати `_ui-primitives.scss`.
- [x] 060 — Dashboard звітів: приватний `/reports`, server-driven список, пошук, швидкі статуси звіту та двостанова проєкція продажу «Продано / Не продано», розширені фільтри 4C/форми/діапазонів/дат, RBAC, URL-параметри, пагінація, клікабельні server-side сортування, вітрина з 4C/бейджами й demo-ціною `USD … d`, а також меню дій `⋮`; приватний detail/edit/print залишаються 080.
- [x] 070 — Майстер створення звіту: три кроки, серверні довідники, `examination_date`, preview наступного ID, live IDC preview, детермінований demo-прогноз `USD … d`, валідація, приватні вкладення та підтверджене ручне збереження `draft`. Detail/edit, commercial state і transitions лишаються 080.
- [x] 080 — Приватний перегляд і редагування: `/report-detail.html`, private owner/admin RBAC, draft-редагування повного контракту, детальний `market_status`, вкладення, history та lifecycle actions. Кожний успішний `PUT /reports/{id}` додає `report_updated`; `issued` доступний admin лише за видимих expert-confirmed grades. Друк не входив у цей зріз.
- [x] 085 — Прибирання legacy API: `/diamonds/*`, unreachable frontend handler, старі Pydantic/CRUD контракти й demo `MLService` вилучені. Historical legacy-колонки залишені без міграції; їхню межу, retirement write-скрипта та умови можливого майбутнього diff/write-flow зафіксовано у 120 / ADR-004.
- [x] 090 — Публічний паспорт і QR: окрема public projection `GET /public/passports/{public_id}`, непередбачуваний revocable token, admin publish/revoke/reissue, SVG QR і `passport.html`. Не відкриває ціну, персональні чи внутрішні дані.
- [x] 095 — Передача публічного паспорта та PDF: admin бачить і копіює код/URL, landing приймає лише код, а пряме посилання й посилання з QR відкривають паспорт напряму. Server генерує on-demand allow-listed PDF для поточного active issued report. Старі код/QR/URL не підходять після reissue; revoke і void закривають нове завантаження.
- [x] 100 — Профіль і admin UI: profile ПІБ/password, admin roles і reversible deactivate; versioned довідники — 105, статистика — 108.
- [x] 105 — Версії правил IDC і довідників оцінювання: зафіксовані межі `idc-demo-v1`, одне джерело expert grades, immutable ruleset і стабільність historical reports, паспортів та PDF. Редагований admin-каталог формул/меж не реалізований: нова методика оформлюється окремою версією правил.
- [x] 108 — Контракт operational analytics: усунуто 500, admin-only status-агрегати експертів, review-cycle metrics адміністраторів і три вкладки analytics реалізовано та перевірено. Active-time і period filters винесено у 112; stone/ML analytics — у 120.
- [x] 112 — Активний час експертів і періоди: `0011` додає server-timed сесії, append-only events і single-tab lease без historical backfill. Owner-gemologist draft трекається тільки після дії у видимій вкладці; 60-секундний max interval, 75-секундний lease, pause/offline та replacement вкладки виключають простий час очікування й подвоєння. Admin analytics має `date_from`/`date_to`: status counts за `created_at`, active-time за завершенням session, review-cycle за рішенням admin.
- [x] 113 — Час від початку майстра до першого збереження: `0012` додає server-timed pre-save lease та nullable first-save поля майбутнього report без historical backfill. Після першої взаємодії у видимому wizard lease прив'язується атомарно лише до успішного `POST /reports`; replaced/offline/покинута спроба не блокує save й не потрапляє в метрику. Admin бачить окремі count/total/average/median, не змішані з active-time draft.
- [x] 110 — Авторитетні ринкові дані: OpenFacet adapter, immutable candidate/approved/rejected snapshot-и, ручний admin flow, provenance та явне прикріплення `market_reference` реалізовано; `0008_market_data_providers` застосовано до локальної MariaDB. Кожен фактично створений ринковий орієнтир фіксується append-only private подією; старі valuation не отримують вигаданого backfill. Demo `USD … d`, historical `price`, public passport і PDF не змінюються автоматично.
- [x] 121 — Розширення ринкових провайдерів і FX: НБУ USD/UAH fetch/ручний refresh, immutable FX snapshot і policy майбутніх системних орієнтирів реалізовано у `0009`/`0010`. Admin обирає market provider radio-кнопкою та вмикає/вимикає UAH-конвертацію НБУ; майстер preview читає цю policy й показує нефіксований USD-орієнтир. Підтримуваний новий або змінений draft отримує `system_market_reference` з останнього approved snapshot-а policy, а ручний `market_reference` лишається пріоритетним. Dashboard/private detail показують provenance. Операційний контур завершено у 122; його актуальний опис — [market-data-providers.md](./guides/market-data-providers.md).
- [x] 122 — Операційний контур ринкових провайдерів: `0013` додає admin-configurable графіки та freshness-пороги OpenFacet/НБУ, append-only журнал спроб і CLI для зовнішнього scheduler-а. OpenFacet створює лише candidate, НБУ дедуплікує rate/date; retries 15/30/60 хв. Збереження/редагування звіту не викликає мережу і бере лише cached FX, що не перевищив block-поріг. Historical valuation, report, public passport і PDF не переписуються.
- [x] 115 — UI-polish профілю та admin UI: shared primitives уніфікують primary/outline кнопки та interactive-стани полів; password-toggle у login, Profile і admin-формах має помітні hidden/visible SVG, фон, `aria-label` і `aria-pressed`. Перевірено desktop, tablet і mobile без зміни API чи бізнес-логіки.
- [x] 120 — Legacy-перерахунок і межа ML: `recalc_grades.py` retired, бо він переписував усі legacy-поля без dry-run/scope/audit/rollback і не працював із чинним `Stone`/system/expert контрактом. Historical projections не очищаються й не backfill-яться. Нова IDC-версія — forward-only; будь-який майбутній diff/write-flow потребує окремого рішення, dry-run, scope, audit trail, backup і rollback. `ml_results` лишається порожнім reserved schema до ліцензованого, versioned і відтворюваного ML/SOM-контракту ([ADR-004](./decisions/004-legacy-calculation-and-ml-boundary.md)).
- [x] 130 — Публічні вкладення паспорта: admin може явно опублікувати лише `stone_photo` або `plotting_diagram` виданого report. Anonymous endpoint прив'язаний до active passport token, allow-list-ить JPEG/PNG/WebP, звіряє SHA-256 та повертає `no-store`; private/revoked/void/tampered media дає 404. PDF не містить вкладень.
- [x] 131 — Зображення у PDF публічного паспорта: on-demand PDF додає лише чинні явно опубліковані фото каменю та plotting після основної сторінки, з allow-list/checksum/revoke гарантіями, A4 layout і PDF-тестами. PDF не є snapshot-ом: зняте з публікації медіа відсутнє лише в наступних генераціях.
- [x] 132 — Публічні інформаційні сторінки: footer веде на responsive «Політику конфіденційності» фактичного local MVP і довідку про код/URL/QR/PDF паспорта. Production/legal деталізація потребує окремого рішення після вибору хостингу й процесів даних.
- [x] [133 — Release-аудит local MVP](./reviews/2026-09-24-local-mvp-release-audit.md): критичних знахідок немає; schema convergence завершено у 134, deterministic passport contract та isolated real browser E2E — у 135.
- [x] 134 — Збіжність Alembic, ORM і MariaDB: read-only інвентаризація підтвердила canonical MariaDB індекси на `0013`; ORM metadata скориговано без DDL/new revision, `alembic check` green і regression test фіксує імена ключів.
- [x] 135 — Реальний browser E2E і контракт паспорта: stale mock синхронізовано з `{ passport: ... }`; disposable SQLite runtime виконує реальний workflow без MariaDB, user records або `seed_db.py`.
- [ ] [136 — SQLAlchemy/Pydantic deprecation cleanup](./backlog/136-sqlalchemy-pydantic-deprecation-cleanup.md): прибрати підтверджені warnings без зміни API чи schema.
- [ ] [141 — IDEX Online trial readiness](./backlog/141-idex-online-trial-readiness-and-mockup.md): English mock-up, attribution/branding boundary, private provider contract і staging-ready activation 30-day trial.
- [ ] [145 — Контракт мультимовності](./backlog/145-internationalization-contract.md): English-first/Ukraine presentation layer без втрати form state чи зміни доменних даних; реалізація після рішення 160.

### Пріоритет 4 — перевірений ML, PostgreSQL і тестовий домен

- [x] **mariadb-local-recovery:** локальний MariaDB відновлено в поточному
  XAMPP через чистий `mysql/data` та перевірені SQL-дампи. Відновлено три
  бази Diamant ID і три інші користувацькі бази; старий data-directory
  збережено окремим архівом. Runbook:
  [mariadb-local-recovery.md](./guides/mariadb-local-recovery.md).
- [ ] Відокремити конфігурацію БД від MariaDB-специфічного коду, зберігши локальну MariaDB.
- [ ] Після локального MVP реалізувати перевірений ML-контур: датасет, versioned model artifact, валідація метрик, відтворюваний прогноз і окремі аналітичні результати.
- [ ] [150 — Analytics і verified ML strategy](./backlog/150-analytics-and-verified-ml-strategy.md): спершу dataset/data-quality/target і baseline, потім model artifact/validation, а stone/SOM UI лише після валідних результатів.
- [ ] [160 — Platform і stack decision](./backlog/160-platform-and-stack-decision.md): після локально верифікованого ML підтвердити FastAPI + Gulp/Pug/JS для staging, cloud topology та критерії майбутнього Vite/TypeScript без передчасного rewrite.
- [ ] [161 — PostgreSQL migration і staging](./backlog/161-postgresql-migration-and-staging.md): після 150 і рішення 160 виконати migration, integrity/dry-run/rollback, staging runtime й інтеграцію 140 scheduler-а.
- [ ] Перевірити PostgreSQL-діалект, перенести тестові дані та звірити кількість/цілісність записів.
- [ ] [140 — Хмарне розгортання та scheduler ринкових даних](./backlog/140-cloud-deployment-and-provider-scheduler.md): після 150 → 160 → 161 обрати staging/cloud runtime, налаштувати deployment, secrets, managed scheduler кожні 5 хвилин для provider CLI, logs/alerts і runbook; локальний Windows Task Scheduler не є ціллю.
- [ ] Налаштувати CORS, env secrets, health-check, домени/TLS та ручний smoke-test до публічного запуску.

### Зафіксовані розбіжності з початковими нотатками

- Нотатки описують локальний backend у Docker, але поточний репозиторій запускає FastAPI напряму з `.venv`; Docker ще не реалізований.
- `diamond_analytics.ml_results` має SQLAlchemy-модель і відтворюється порожньою local seed; API, dataset/model artifact, запис і ML-потік для неї відсутні.
- Публічний passport/QR, allow-listed PDF і контрольована публічна видача двох типів зображень реалізовані окремими safe flow; profile/admin UI також реалізовано. Full private print і ML-аналітика ще не присутні як завершений код у репозиторії.

### Рішення щодо гілок

- `local-dev`: базова гілка локальної розробки з MariaDB.
- `main`: майбутній deploy-кандидат для PostgreSQL; merge лише після локальних перевірок і окремого плану розгортання.
- Робота ведеться в короткоживучих task-гілках від `local-dev`; гілка `agent-project-foundation` — перехідна для цього налаштування.

---
