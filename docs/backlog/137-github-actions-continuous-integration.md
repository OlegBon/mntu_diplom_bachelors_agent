# 137 — GitHub Actions continuous integration

## Мета

Зробити GitHub Actions критерієм безпечного переходу з `local-dev` до майбутнього
`main`: зміна, яку готують до merge, має відтворювано проходити backend,
frontend, документаційні та browser-перевірки. Це CI, а не deployment pipeline.

Поки локальна розробка активно розбивається на малі task-коміти, CI не повинен
витрачати GitHub-hosted minutes на кожен `push` у кожну тимчасову гілку.

## Передумови

- Локальні `pytest`, `npm test`, mock Playwright і isolated real E2E існують;
  real E2E використовує disposable SQLite та не потребує MariaDB secrets.
- `alembic check` має виконуватись проти окремого ephemeral MariaDB service,
  після `alembic upgrade head`; CI ніколи не підключається до локальної чи
  production БД.
- `main` ще не є deploy-контуром. Branch protection налаштовується лише після
  того, як workflow успішно перевірено у GitHub.
- Реальний час одного запуску ще не виміряний у GitHub. До ввімкнення workflow
  власник репозиторію перевіряє його поточний тариф і включені GitHub Actions
  minutes/storage; безкоштовні ліміти залежать від типу репозиторію й плану.

## Момент увімкнення та економний режим

- Реалізація 137 є gate перед першим PR з `local-dev` до `main` і не пізніше
  початку staging-задачі 161. До цього локальні checks та явні merge-коміти
  лишаються достатнім контуром.
- Перший повний workflow запускається лише через `pull_request` до `local-dev`
  або `main` та через `workflow_dispatch`. Повний набір не запускається на
  кожен `push` у task-гілку.
- Workflow має workflow-level `concurrency` за workflow+ref з
  `cancel-in-progress: true`: новий commit того самого PR скасовує застарілий
  незавершений run.
- Використовуються лише standard Linux runners. Успішні runs не завантажують
  артефакти; Playwright trace/screenshot збираються лише при failure та мають
  короткий retention.
- Після перших п'яти зелених runs фіксуються фактичні minutes/storage. У
  налаштуваннях GitHub мають бути встановлені usage alerts (90/100 %) і
  обмеження витрат, перш ніж checks стануть required.

## Scope

- Додати full workflow на pull request до `local-dev` / `main` та ручний
  `workflow_dispatch`; після появи `main` застосовувати той самий набір
  required checks. Post-merge `push` smoke може бути окремим легким workflow
  лише за окремим рішенням і не дублює full CI.
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
