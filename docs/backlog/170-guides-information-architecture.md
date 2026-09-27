# 170 — Guides information architecture

## Мета

Зробити `docs/guides/` практичною, короткою документацією «як система
працює зараз», не розмиваючи роль ADR, architecture, backlog або progress.

## Scope

- Додати й підтримувати guides для реалізованих користувацьких та
  операційних сценаріїв: SOM/demo analytics, frontend, backend/API, database
  operations і testing.
- Переносити з `architecture.md` лише пояснення фактичної поведінки,
  запуску, обмежень і прикладів; architecture зберігає компоненти, data flow,
  межі систем і посилання.
- Лишати в `decisions/` незмінними рішення та причини, у `work_plan.md` —
  коротку дорожню карту, у `backlog/` — майбутню роботу, у `progress.md` —
  хронологію доказів.
- Для кожного перенесеного розділу залишати коротке посилання-заміщення,
  перевіряти локальні Markdown links та не дублювати одну норму у кількох
  місцях.

## Кандидати

| Джерело | Майбутній guide | Що переноситься |
| --- | --- | --- |
| `architecture.md`, frontend правила | `frontend-guide.md` | Gulp/Pug/SCSS/JS, сторінкові modules, API client, UI states. |
| `architecture.md`, `api-mvp-audit.md` | `backend-api-guide.md` | auth/RBAC, route conventions, errors, domain API boundaries. |
| `architecture.md`, `db-schema.md`, `local-start.md` | `database-guide.md` | schemas, Alembic lifecycle, local-safe operations, backup boundaries. |
| `architecture.md`, testing rules | `testing-guide.md` | pytest/SQLite isolation, Node/jsdom, Playwright, local verification. |
| ADR-005, 159 result | `synthetic-som-demo.md` | implemented SOM explanation; created now and updated with 159. |

## Готовність

Кожен guide описує лише перевірену поточну поведінку, має links до source
decision/backlog, проходить `python scripts/check_doc_links.py` і не містить
секретів або застарілих команд.
