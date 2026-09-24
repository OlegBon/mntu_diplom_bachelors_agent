# 133 — Release-аудит local MVP

## Мета

Підтвердити, що завершений local MVP придатний як цілісний локальний workflow,
і перетворити всі підтверджені прогалини на окремі пріоритетні задачі.

## Scope

- Code review: RBAC, report lifecycle, public passport/QR/PDF/media, errors і межі модулів.
- Документація: `architecture`, guides, runbooks, backlog і фактична поведінка.
- Тести: critical API paths, DOM/Playwright, перелік не покритих реальних flows.
- Local runtime: MariaDB/Alembic/startup/recovery, без запуску destructive seed.
- Security/UX review: public-data boundary, secret hygiene, desktop/mobile/accessibility.
- Окремо спланувати реальний browser E2E з MariaDB і безпечною test-auth стратегією.

## Правила

- Аудит спершу фіксує докази, пріоритет і рішення; не перетворюється на
  неявний масовий рефакторинг.
- Кожна підтверджена проблема отримує окремий backlog-файл; зміни лише після
  погодженого scope.

## Критерії готовності

- Є короткий audit report і актуальний список нових fix-задач або явний висновок,
  що критичних знахідок немає.
- `work_plan`, docs і тести не суперечать фактичному local MVP.
