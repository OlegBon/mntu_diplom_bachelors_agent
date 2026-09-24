# 161 — PostgreSQL migration і staging

## Мета

Перенести підтверджений local контур MariaDB до перевіреного PostgreSQL staging
після рішення 160, без втрати даних або зміни domain behavior.

## Scope

- MariaDB/PostgreSQL schema compatibility (після [134](./134-alembic-schema-convergence.md)), Alembic plan, test data migration,
  row counts, integrity checks, dry-run і rollback.
- Docker/runtime config, production env/secrets, exact CORS, healthcheck,
  backups, TLS/domain і manual staging smoke test.
- Інтегрувати [140](./140-cloud-deployment-and-provider-scheduler.md) як managed
  scheduler provider CLI після готової staging DB.

## Поза межами

- Переписування FastAPI або frontend framework.
- ІDEX activation до 141 і готового isolated staging.
