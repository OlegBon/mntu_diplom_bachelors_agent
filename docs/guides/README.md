# Guides

Ця папка пояснює, **як Diamant ID працює насправді**: для користувача,
розробника та того, хто перевіряє сценарії. Вона не замінює технічну
[архітектуру](../architecture.md), журнал [progress](../progress.md), активний
[backlog](../backlog/README.md) або архітектурні [рішення](../decisions/).

## Правило актуальності

- Guide описує реалізовану поведінку й її відомі межі.
- Майбутня поведінка посилається на backlog або ADR і позначається як
  запланована.
- Після зміни сценарію, API або даних відповідний guide оновлюється разом із
  кодом і `docs/progress.md`.

## Наявні guides

| Файл | Призначення |
| --- | --- |
| [current-domain-and-report-workflow.md](./current-domain-and-report-workflow.md) | Повний актуальний шлях звіту: ролі, wizard, поля, IDC, statuses/review, private media, public passport, код/URL/QR, PDF та межі публічних даних. |
| [idc-demo-v1-ruleset.md](./idc-demo-v1-ruleset.md) | Межі `idc-demo-v1`, матриця IDC 2013, джерела expert grades і безпечне оновлення ruleset. |
| [demo-dataset-operations.md](./demo-dataset-operations.md) | Ізоляція synthetic demo dataset, scope, manifest, inventory, backfill і rollback межі. |
| [historical-synthetic-safety.md](./historical-synthetic-safety.md) | Підтверджений вручну allow-list, read-only dry-run, logical backup і disposable restore перед можливим historical scope backfill. |
| [synthetic-som-demo.md](./synthetic-som-demo.md) | Як працює ізольована SOM-карта, policy scenario, artifact, UI та межі щодо real analytics. |
| [synthetic-demo-provider-analytics.md](./synthetic-demo-provider-analytics.md) | Ізольована analytics fictional Demo Market A/B і scope-bound контракт для майбутніх дозволених real data. |
| [mariadb-local-recovery.md](./mariadb-local-recovery.md) | Безпечний перехід з аварійного XAMPP MariaDB у чисте локальне середовище через SQL-дампи. |
| [frontend-guide.md](./frontend-guide.md) | Pug/SCSS/JavaScript, Gulp, API client і UI-примітиви з фрагментами коду. |
| [backend-api-guide.md](./backend-api-guide.md) | FastAPI route → JWT/RBAC → CRUD, API boundaries та приклади коду. |
| [database-guide.md](./database-guide.md) | SQLAlchemy schemas, Alembic lifecycle, seed і database boundaries з прикладами. |
| [database-topology.md](./database-topology.md) | Contract трьох local MariaDB databases і однієї майбутньої PostgreSQL database з трьома schemas, grants, backup та вхід для 161. |
| [testing-guide.md](./testing-guide.md) | Ізольовані pytest, jsdom, Playwright і verification matrix. |
