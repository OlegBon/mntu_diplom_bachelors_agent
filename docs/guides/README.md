# Guides

Ця папка пояснює, **як Diamant ID працює насправді**: для користувача,
розробника та того, хто перевіряє сценарії. Вона не замінює технічну
[архітектуру](../architecture.md), журнал [progress](../progress.md), активний
[backlog](../backlog/README.md) або архітектурні [рішення](../decisions/).

## Правило актуальності

- Guide описує реалізовану поведінку й її відомі межі.
- Майбутня поведінка посилається на backlog або ADR і позначається як
  запланована.
- Після зміни сценарію, API або даних відповідний guide оновлюється разом із
  кодом і `docs/progress.md`.

## Наявні guides

| Файл | Призначення |
| --- | --- |
| [current-domain-and-report-workflow.md](./current-domain-and-report-workflow.md) | Поточні ролі, звіти, IDC-розрахунок, ціна, dashboard, медіа та межі реалізації. |
| [mariadb-local-recovery.md](./mariadb-local-recovery.md) | Безпечний перехід з аварійного XAMPP MariaDB у чисте локальне середовище через SQL-дампи. |

## Заплановані guides

- `frontend-guide.md` — Pug, SCSS, JavaScript, Gulp, сторінки та API-клієнт.
- `backend-api-guide.md` — FastAPI, JWT, RBAC, контракти й помилки API.
- `database-guide.md` — MariaDB-схеми, seed, майбутні Alembic-міграції.
- `testing-guide.md` — pytest, JS/DOM, Playwright і межі тестового контуру.

Ці файли додаються лише тоді, коли їхній зміст буде звірено з кодом; назви не
означають, що відповідний guide або функціонал уже реалізовано.
