# 161 — PostgreSQL migration і staging

## Мета

Перенести підтверджений local контур MariaDB до перевіреного PostgreSQL staging
після локального verified ML experiment за [152](./152-verified-ml-experiment.md)
та platform decision 160, без втрати даних або зміни domain behavior.

## Scope

- MariaDB/PostgreSQL schema compatibility (після завершеної 134 schema convergence), Alembic plan, test data migration,
  row counts, integrity checks, dry-run і rollback.
- Docker/runtime config, production env/secrets, exact CORS, healthcheck,
  backups, TLS/domain і manual staging smoke test.
- Інтегрувати [140](./140-cloud-deployment-and-provider-scheduler.md) як managed
  scheduler provider CLI після готової staging DB.

Перед першою disposable PostgreSQL перевіркою застосувати погоджений
[database topology contract](../guides/database-topology.md): одна physical
database, schemas `diamond_oltp`/`diamond_market`/`diamond_analytics`, окремі
bootstrap/migration/runtime roles, один explicit PostgreSQL `DATABASE_URL`,
cross-schema FK/integrity test і verified backup/restore. `DB_NAME` не є
production fallback.

## Поза межами

- Переписування FastAPI або frontend framework.
- IDEX activation без окремого письмового provider approval і готового isolated staging.
