# 137 — GitHub Actions continuous integration

## Мета

Зробити GitHub Actions критерієм безпечного переходу з `local-dev` до майбутнього
`main`: кожна зміна має відтворювано проходити backend, frontend, документаційні
та browser-перевірки до merge. Це CI, а не deployment pipeline.

## Передумови

- Локальні `pytest`, `npm test`, mock Playwright і isolated real E2E існують;
  real E2E використовує disposable SQLite та не потребує MariaDB secrets.
- `alembic check` має виконуватись проти окремого ephemeral MariaDB service,
  після `alembic upgrade head`; CI ніколи не підключається до локальної чи
  production БД.
- `main` ще не є deploy-контуром. Branch protection налаштовується лише після
  того, як workflow успішно перевірено у GitHub.

## Scope

- Додати workflow на `push` до `local-dev` і на pull request до `local-dev` /
  `main`; після появи `main` застосовувати той самий набір required checks.
- Розділити jobs або кроки так, щоб було видно джерело помилки:
  Python install + `pytest`, MariaDB/Alembic schema check, frontend build/Node,
  mock Playwright, isolated real Playwright, Markdown links.
- Використати зафіксовані версії Actions і Python/Node, dependency caching,
  Playwright browser install та artifacts для screenshot/trace лише при падінні.
- Описати в runbook локальні еквіваленти команд і CI-only MariaDB bootstrap.
- Після зеленого запуску зафіксувати рекомендовані required checks для `main`:
  backend, schema, frontend, mock E2E, real E2E та docs links.

## Поза межами

- Deploy, Docker image registry, cloud credentials, IDEX key, production secrets
  або scheduled provider jobs.
- Автоматичні migrations на будь-якій постійній БД.
- GitHub branch protection через API без окремого підтвердження власника repo.

## Критерії готовності

- Workflow проходить у GitHub на clean runner і відтворює локальні quality gates.
- Невдалий тест дає зрозумілий job log, а browser failure залишає потрібний artifact.
- CI не має доступу до користувацьких MariaDB даних, `.env` або production secrets.
- Документація пояснює, які checks мають бути required перед merge у `main`.
