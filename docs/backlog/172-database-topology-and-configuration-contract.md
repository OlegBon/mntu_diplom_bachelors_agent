# 172 — Database topology і configuration contract

## Мета

Прибрати неоднозначність local database configuration і зафіксувати цільову
topology перед PostgreSQL/staging: три MariaDB databases локально відповідають
одній PostgreSQL/cloud database з трьома логічними schemas.

## Погоджена topology

| Середовище | Фізичний контейнер | Логічні межі |
| --- | --- | --- |
| Local MariaDB | Три databases на одному server | `diamond_oltp`, `diamond_market`, `diamond_analytics` |
| PostgreSQL / cloud | Одна database | schemas `diamond_oltp`, `diamond_market`, `diamond_analytics` |

`DB_NAME=diamond_oltp` у local `.env` — лише default database для одного
SQLAlchemy connection URL, а не повний перелік даних застосунку. Моделі
використовують schema-qualified table names, тому DB-користувач повинен мати
мінімально необхідні права на всі три local databases. Для cloud достатній
один `DATABASE_URL`; schemas не зливаються в `public` без окремого ADR.

## Scope

- Аудит і вирівнювання `.env.example`, `local-start`, `architecture`,
  `db-schema`, scripts bootstrap/seed/backup/restore та Alembic instructions.
- Явно описати local MariaDB database ↔ PostgreSQL schema mapping, default
  connection database, потрібні least-privilege права та ownership migrations.
- Вирішити, чи лишається `DB_NAME` як compatibility name, чи отримує
  безпечний alias/rename без ламаючої зміни приватних `.env`.
- Зафіксувати table ownership: demo SOM artifacts належать
  `diamond_oltp`; `diamond_analytics.ml_results` не є контейнером demo SOM і
  залишається reserved до окремого verified analytics contract.
- Скласти точний input для 161: schema creation, migration order,
  cross-schema foreign keys, grants, backups, restore verification і rollback.

## Поза межами

- Фізична PostgreSQL migration, cloud provisioning, перенесення або backfill
  даних — це 161 після 160/137.
- Нові таблиці ML/SOM, зміна domain logic, seed даних, RBAC або provider policy.
- Злиття всіх логічних schemas у одну таблицеву область `public`.

## Залежності та порядок

- Може бути виконана як документаційний/конфігураційний аудит до 161.
- Не залежить від реального ML dataset, але її висновки є input для 160 і
  обов'язковим baseline для 161.
- 161 не починає PostgreSQL schema/data migration, доки contract не
  погоджено й не перевірено на disposable PostgreSQL instance.

## Критерії готовності

- Новий локальний розробник розуміє, чому один `DB_NAME` не скасовує трьох
  MariaDB databases, і які grants потрібні без читання коду моделей.
- Документація однозначно показує одну cloud database та три PostgreSQL schemas.
- `ml_results`, demo SOM artifacts, Alembic/seed/backup ownership не мають
  суперечливих описів.
- Посилання, config smoke-check і, за потреби, disposable schema smoke-test
  проходять без торкання цінних локальних даних.
