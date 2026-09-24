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

## Поза межами

- Переписування FastAPI або frontend framework.
- ІDEX activation до 141 і готового isolated staging.
