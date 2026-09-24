# 136 — SQLAlchemy і Pydantic deprecation cleanup

## Мета

Прибрати підтверджені runtime warnings SQLAlchemy 2 і Pydantic 2 без зміни
API-контрактів, доменної логіки чи даних.

## Підтверджений стан

Поточний `pytest` проходить, але показує:

- SQLAlchemy `declarative_base()` перенесено до `sqlalchemy.orm`;
- Pydantic v2 deprecates class-based `Config` на користь `ConfigDict`;
- слід також інвентаризувати застаріле `.dict()` і замінювати його лише там,
  де еквівалент `model_dump()` не змінює serialization behavior.

## Scope

- Мінімально оновити імпорти й model configuration до підтримуваного API.
- Звірити Pydantic serialization, aliases, ORM/from-attributes і OpenAPI
  responses API/integration тестами.
- Перевірити повний pytest, frontend API client tests і FastAPI import.
- Оновити документацію лише якщо змінюється сумісність конфігурації.

## Поза межами

- Upgrade major version FastAPI, SQLAlchemy або Pydantic.
- Зміна request/response JSON, БД-схеми, domain rules або frontend behavior.

## Критерії готовності

- Зазначені deprecation warnings не з'являються в pytest.
- API regression tests підтверджують незмінні контракти.
- Нових migration або environment variables немає.
