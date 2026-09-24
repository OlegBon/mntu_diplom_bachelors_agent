# Release-аудит local MVP — 24 вересня 2026

## Висновок

Локальний MVP має цілісний private workflow звіту, public passport/QR/PDF,
media allow-list, ринкові snapshot-и та базові RBAC межі. Критичних
функціональних або підтверджених витоків даних у виконаному зрізі не знайдено.
Водночас release не варто вважати готовим до staging, доки не реалізовано
реальний browser E2E.

## Виконані перевірки

- `python -m pytest` — 62 тестів пройшли (SQLite in-memory API/integration).
- `frontend npm test` — 22/22 пройшли; build успішний.
- `npm run audit:api` проти `127.0.0.1:8000` — 18/18 read-only/CORS
  перевірок пройшли.
- Повний Playwright — 16/17: знайдено застарілий mock-контракт паспорта,
  винесено у [135](../backlog/135-real-browser-e2e-and-passport-contract.md).
- `alembic current` — `0013_market_provider_operations (head)`; початкова
  index/metadata розбіжність усунена metadata correction без DDL, а
  `alembic check` проходить.
- `python -m compileall -q backend scripts` — пройшов.
- Внутрішні Markdown-посилання перевіряються
  `python scripts/check_doc_links.py`.

## Знахідки та рішення

### Вирішено — Alembic schema convergence

`alembic check` початково бачив remove/add index operations для
`public_passports`, `report_work_session_events` і
`market_provider_operations`, хоча runtime DB вже на head. Read-only
інвентаризація підтвердила: MariaDB відповідає canonical Alembic revisions,
а зайві ORM `index=True`/неназвана unique metadata були джерелом false drift.
Metadata приведена у відповідність без DDL; `alembic check` green і regression
test фіксує canonical names.

### Середньо — browser E2E не є green

Passport delivery test повертав стару raw JSON форму, а private API тепер
повертає wrapper `passport`. Це тестова, не UI-регресія, але вона приховує
цінний сценарій PDF/QR. Виправлення mock-а й ізольований real E2E flow
належать [135](../backlog/135-real-browser-e2e-and-passport-contract.md).

### Низько — tooling debt

Frontend build попереджає про застарілий Sass `@import` і Browserslist data.
Це не зупинило build або тести. Міграцію Sass та оновлення залежностей слід
планувати разом із рішенням про Vite/TypeScript у [160](../backlog/160-platform-and-stack-decision.md),
без механічного churn у release-аудиті.

## Security і public-data boundary

- JWT secret обов'язковий через конфігурацію; паролі перевіряються bcrypt,
  inactive accounts не проходять login/JWT.
- RBAC перевіряється server-side; media storage не монтується статично;
  public media обмежено типами, active issued passport token-ом і SHA-256.
- Frontend будує динамічний вміст через `textContent`/DOM, а external provider
  links мають `noopener noreferrer`.
- Поточний CORS regex навмисно дозволяє лише `localhost`/`127.0.0.1` з портом
  для local MVP. До staging потрібні exact allowed origins, trusted public
  app origin для QR URL, TLS, secrets і production auth hardening — це scope
  [161](../backlog/161-postgresql-migration-and-staging.md).

## Межі цього аудиту

Не виконувалися destructive seed, migration, ручний DDL, зовнішні provider
requests, penetration testing або real browser scenario з MariaDB. API audit
навмисно не робить authenticated POST/PUT/DELETE. Публічний production launch,
IDEX activation і PostgreSQL не входять до local MVP.
