# Журнал змін Diamant ID

Журнал фіксує зміни та перевірки Diamant ID.

Нові записи завжди додаються одразу під цим абзацом — у зворотному хронологічному порядку.

## 2026-09-14 — api-and-mvp-audit (завершено)

- **Задача:** провести аудит усіх API-маршрутів, auth/RBAC, frontend ↔ API, MariaDB-схеми та seed без зміни даних; оновити план робіт рішенням для кожного endpoint-а.
- **Змінені файли:** `docs/api-mvp-audit.md`, `docs/work_plan.md`, `docs/progress.md`.
- **Результат:** зафіксовано статус і дію для всіх OpenAPI маршрутів, критичні дефекти створення звіту/RBAC, UI-розбіжності, legacy seed і schema drift `diamond_analytics.ml_results`; повних API-дублікатів не знайдено.
- **Перевірки:** статичний аналіз backend/frontend/seed; read-only інспекція MariaDB; `npm run audit:api` — 6/10 на вже відкритому `:8000` (DB-маршрути зависли) та 10/10 на тимчасовому чистому FastAPI `:8002`; тимчасовий сервер зупинено. POST/PUT/DELETE, login, seed, SQL-мутації та E2E не запускалися.

## 2026-09-13 — mcp-guidance (завершено)

- **Задача:** актуалізувати правила MCP в `AGENTS.md`, щоб вони не покладалися на статичний список серверів із іншого середовища.
- **Змінені файли:** `AGENTS.md`, `docs/progress.md`.
- **Результат:** джерелом істини визначено доступні інструменти активної сесії; `codex mcp list` залишено необов’язковою перевіркою за наявності налаштованого CLI; додано межі використання MCP і зовнішніх дій.
- **Перевірки:** `codex mcp list` у поточному shell не запускається через відсутній доступний CLI home/CODEX_HOME; це зафіксовано як обмеження середовища, без зміни глобальної конфігурації. `git diff --check` успішний.

## 2026-09-13 — technical-specification (завершено)

- **Задача:** створити технічний опис Diamant ID у стилі `tech_saas.md` з Convertly Hub, але за фактичним стеком і планами Diamant ID.
- **Змінені файли:** `docs/tech_diamant_id.md`, `docs/progress.md`.
- **Результат:** зафіксовано можливості локального MVP, стек, локальну інфраструктуру, API і дані, політику безпеки, межі готовності та окремий планований PostgreSQL/deploy-контур.
- **Перевірки:** звірено з `docs/architecture.md`, `docs/local-start.md`, `docs/work_plan.md`, кодом backend/frontend і наданим прикладом; внутрішні посилання й `git diff --check` успішні.

## 2026-09-13 — architecture-refresh (завершено)

- **Задача:** переписати `docs/architecture.md` у розгорнутому стилі прикладу Convertly Hub, спираючись на фактичний код Diamant ID.
- **Змінені файли:** `docs/architecture.md`, `docs/progress.md`.
- **Результат:** описано компоненти, потоки даних, структуру папок, локальний runtime, API/JWT/RBAC, MariaDB-схеми, IDC і демо-ML, межі реалізації та майбутній PostgreSQL/deploy-контур; реалізований стан відокремлено від планів.
- **Перевірки:** вручну звірено backend, seed, Gulp, frontend API-модулі та локальний runbook; `git diff --check` успішний.

## 2026-09-13 — local-api-audit (завершено)

- **Задача:** адаптувати успадкований Node.js API-аудитор під локальний FastAPI Diamant ID і додати команду запуску та документацію.
- **Змінені файли:** `scripts/audit-api.mjs`, `frontend/package.json`, `.gitignore`, `.codex/skills/api-response-auditor/SKILL.md`, `AGENTS.md`, `docs/progress.md`.
- **Межі:** лише `localhost`/`127.0.0.1` через HTTP; GET та CORS preflight. Скрипт не виконує login, POST, PUT, DELETE, seed або запити з токеном.
- **Перевірки:** `node --check scripts/audit-api.mjs` успішний; `npm run audit:api` проти тимчасового FastAPI на `127.0.0.1:8002` і стандартного локального API на `127.0.0.1:8000` — 10/10 перевірок пройдено; віддалений URL відхиляється до виконання запитів; `git diff --check` успішний.
- **Нові змінні середовища:** опційна `API_AUDIT_BASE_URL` тільки для іншого локального порту.

## 2026-09-13 — agent-guidance-audit (завершено)

- **Задача:** повторно дослідити стек Diamant ID, звірити rules і skills зі структурою Convertly Hub та оновити інструкції агента без перенесення чужих технологічних припущень.
- **Змінені файли:** `AGENTS.md`, `.codex/rules/{python-backend,frontend,database,security,testing,verification,local-architecture,local-quality-and-performance}.md`, `.codex/skills/{api-response-auditor,postgres-patterns,frontend-patterns,diamond-domain-rules,python-patterns,python-testing,database-reviewer,database-migrations,security-review,web-performance}/SKILL.md`, `docs/progress.md`.
- **Результат аудиту:** підтверджено стек FastAPI + SQLAlchemy 2 + MariaDB/XAMPP, Pydantic і JWT; Gulp 5 + Pug + SCSS + vanilla JavaScript + BrowserSync. React, Next.js, Prisma, їхні hooks і правила не застосовні. Автоматичного `audit:api` скрипта та test suite немає.
- **Рішення:** додано правила архітектури й якості/продуктивності, skills `frontend-patterns` і `diamond-domain-rules`, актуалізовано API-аудит і PostgreSQL-патерни для SQLAlchemy. Кожен ключовий skill містить контекст, межі, порядок роботи й очікуваний результат без чужих React/Prisma-припущень. Приклад `.codex/convertly-hub` лишено недоторканим і не зроблено частиною канонічних інструкцій Diamant ID.
- **Перевірки:** структура репозиторію, `README.md`, `docs/architecture.md`, Python- і Node-залежності, Gulp-конфігурація та імпорти коду звірені читанням і пошуком; імпорт `backend.main:app` і `npm run build` успішні. Усі 11 локальних skills проходять `skill-creator/scripts/quick_validate.py` у UTF-8 режимі; `git diff --check` успішний. `caniuse-lite` повідомляє про застарілу базу браузерів, але це не блокує збірку.
- **Нові змінні середовища:** немає.

## 2026-09-13 — login-cors-fix (завершено)

- **Задача:** усунути блокування входу в браузері, коли BrowserSync запускається не на порту `3000`.
- **Змінені файли:** `backend/main.py`, `frontend/src/pug/pages/login.pug`, `docs/local-start.md`, `docs/progress.md`.
- **Результат:** CORS дозволяє лише локальні origins `localhost` або `127.0.0.1` з номером порту; браузер отримує заголовок `Access-Control-Allow-Origin` для `http://localhost:3004`. Поля входу мають `autocomplete="username"` і `autocomplete="current-password"`.
- **Перевірки:** імпорт `backend.main:app` успішний; `npm run build` успішний; CORS preflight `OPTIONS /token` з origin `http://localhost:3004` повертає 200 і коректний `Access-Control-Allow-Origin`; `git diff --check` успішний.
- **Нові змінні середовища:** немає.

## 2026-09-13 — runtime-modernization (завершено)

- **Задача:** перевірити локальний запуск на актуальних Python і Node.js, MariaDB, FastAPI та Gulp без руйнівного seed.
- **Змінені файли:** `docs/local-start.md`, `docs/progress.md`.
- **Перевірки:** Python 3.13.7, Node.js 24.18.0, npm 12.0.1; `pip check` успішний; підключення SQLAlchemy до MariaDB 10.4.32 / `diamond_oltp` успішне; FastAPI `GET /` — 200; BrowserSync `GET /` на `localhost:3000` — 200; `npm run build` успішний. Після відтворення `.venv` перевірено `uvicorn 0.40.0` і `GET /` через звичайний launcher — 200.
- **Рішення:** залежності не оновлювалися, бо несумісності не виявлено. Віртуальне середовище відтворено, оскільки launcher `uvicorn` містив шлях до попереднього розташування проєкту. `caniuse-lite` повідомляє про застарілі browser data, але це не блокує запуск і не потребує зміни lockfile в цій задачі.
- **Нові змінні середовища:** немає.

## 2026-09-13 — agent-project-foundation (завершено)

- **Задача:** адаптувати правила агента, skills і документацію під Diamant ID; провести первинний аудит та сформувати актуальний план.
- **Змінені файли:** `AGENTS.md`, `DESIGN.md`, `.codex/rules/*`, `.codex/skills/python-*`, `docs/{architecture,local-start,work_plan,progress}.md`.
- **Перевірки до змін:** `.venv` Python 3.13.7; імпорт `backend.main:app` успішний; `frontend npm run build` успішний. `caniuse-lite` повідомляє про застарілу базу браузерів.
- **Відомі обмеження:** інтеграційний запуск із MariaDB, тестів і deployment ще не виконано. Технічні нотатки з DOCX прочитано та відображено у `docs/work_plan.md`.
- **Нові змінні середовища:** немає.
- **Git:** зміни підготовлено до коміту й злиття в `local-dev`; `main` навмисно не змінюється.

## 2026-09-13 — структура DESIGN і AGENTS

- **Задача:** узгодити структуру `DESIGN.md` і `AGENTS.md` із шаблоном Convertly Hub, не переносячи його технологічні припущення.
- **Змінені файли:** `DESIGN.md`, `AGENTS.md`, `docs/progress.md`.
- **Результат:** `DESIGN.md` містить повний набір секцій design system, прив’язаних до чинних SCSS-токенів Diamant ID. `AGENTS.md` містить повний життєвий цикл задач, локальні skills, MCP, команди й явний стан відсутньої тестової інфраструктури.
- **Перевірки:** структура Markdown і відповідність названим SCSS-токенам перевірені пошуком у репозиторії.
- **Нові змінні середовища:** немає.

---
