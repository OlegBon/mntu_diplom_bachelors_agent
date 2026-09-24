# 134 — Збіжність Alembic, ORM і MariaDB-схеми

## Мета

Відновити release-gate `alembic check`: зафіксована MariaDB на code head має
збігатися з SQLAlchemy metadata без неочікуваних upgrade operations.

## Підтверджений стан

24 вересня 2026 локальна БД має revision `0013_market_provider_operations`,
але `alembic check` виявляє індексні розбіжності для `public_passports`,
`report_work_session_events` і `market_provider_operations`. Зокрема, ORM
декларує окремі `index=True` для primary key/unique полів, тоді як MariaDB
вже має еквівалентні ключі під іншими іменами; також треба звірити складений
індекс provider operation.

## Scope

- Read-only інвентаризація metadata, Alembic revisions та фактичних MariaDB
  `SHOW CREATE TABLE` / `SHOW INDEX` без seed або ручного DDL.
- Визначити для кожної розбіжності: справжній schema drift, діалектну
  особливість autogenerate чи зайву ORM-декларацію.
- Внести мінімальну погоджену revision або скоригувати metadata так, щоб
  `alembic check` був чистим на fresh database і на збереженій local DB.
- Додати regression test/перевірку міграцій та оновити `db-schema.md`.

## Поза межами

- PostgreSQL-перенесення, backfill, cleanup historical даних або зміна
  domain behavior.
- Автоматичне застосування migration до цінної локальної БД без окремого
  підтвердження користувача.

## Критерії готовності

- `alembic current` і `alembic check` проходять на підтримуваній MariaDB.
- Усі index/constraint рішення мають доказ у migration і документації.
- Є безпечний upgrade/downgrade plan для локальної БД.
