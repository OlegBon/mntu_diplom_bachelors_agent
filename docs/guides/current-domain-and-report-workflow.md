# Поточна доменна логіка та workflow звіту

**Стан коду:** 15 вересня 2026 року

Цей guide описує фактичну локальну поведінку Diamant ID, а не цільову модель
із диплома. За стратегічним контрактом звертайтеся до
[ADR-001](../decisions/001-report-domain-contract.md), а за активною
реалізацією — до [work plan](../work_plan.md) і backlog.

## Ролі та межі доступу

| Роль | Фактичні можливості приватного `/reports` API |
| --- | --- |
| `gemologist` | Створює власні `draft`, бачить лише власні reports, редагує власні `draft`, передає їх у `review`, працює з вкладеннями власних `draft`. |
| `admin` | Бачить усі reports, читає та редагує `draft`, може передати `draft` у `review`, керує `review → draft/issued/void` і `issued → void`; не створює первинні звіти. |

Усі приватні маршрути перевіряють JWT. Приховування UI не замінює server-side
RBAC. Гість не має доступу до `/reports`; публічного паспорта або QR ще немає.

## Звіт, камінь і lifecycle

Локальна модель — `Stone → DiamondReport → ReportEvent`. Новий report має
окремий normalized `Stone`; legacy-колонки у `diamond_reports` лишаються
історичною projection даних без активного HTTP API.

Життєвий цикл:

```text
draft --(owner або admin)--> review --(admin)--> issued
                               |                  |
                               +--(admin)--> draft +--(admin)--> void
                               +--(admin)--> void
```

`issued` можливий лише за наявності явно підтверджених експертом proportions і
cut grades. Створення, кожне успішне draft-редагування та status transition
записуються в append-only `ReportEvent` як `created`, `report_updated` або
`status_changed`.

## Створення чернетки

Wizard `/create-report.html` має рівно три кроки: ідентифікація/4C,
геометрія/IDC та висновок/медіа. Він використовує приватні маршрути:

| Маршрут | Призначення |
| --- | --- |
| `GET /reference-values` | Текстові довідники форми, походження, geometry, treatment та identification. |
| `GET /market/mappings` | Числові grade mappings. |
| `GET /reports/next-id` | Нерезервований preview номера; доступний лише gemologist. |
| `POST /reports/preview` | Серверний live IDC preview без збереження. |
| `POST /reports` | Авторитетне створення `draft`; сервер призначає ID. |

`examination_date` за замовчуванням заповнюється поточною датою в UI, але
експерт може вказати фактичну дату дослідження/оцінки. Вона не замінює
технічні `created_at` або `updated_at`.

Новий draft отримує `market_status=not_for_sale`. У private detail/edit owner
або admin може змінити цей стан лише поки звіт `draft`; dashboard показує
спрощену двостанову проєкцію, а detail — повне значення.

## IDC і ціна

`DiamondCalculator` серверно обчислює proportions та фінальний cut за правилом
найгіршого з proportions, polish і symmetry. Це обмежений локальний IDC
розрахунок, а не повна експертна методика IDC 2013.

Preview може повернути `demo_price_usd`. У wizard це позначається як `USD … d`:
`d` означає детермінований демонстраційний прогноз, не ринкову, експертну чи
продажну ціну. Він не зберігається в `DiamondReport.price`.

Для 1 000 legacy demo-записів dashboard показує наявне `price` так само з
позначкою `d`; набір охоплює 01.01.2023–31.12.2025. Його не можна трактувати
як поточне котирування чи автоматично переоцінювати після оновлення довідника.

## Dashboard та наступний UI

Dashboard вже використовує приватний `GET /reports`: server-side pagination,
пошук, фільтри, сортування і RBAC. ID та меню `⋮` ведуть до
`/report-detail.html?id=<report_id>`; для draft доступний режим редагування.
Друк залишається вимкненою окремою дією.

`/diamonds/*` вилучено: dashboard, wizard і detail/edit використовують лише
приватний `/reports`. Legacy-колонки даних не були очищені чи переобчислені;
для цього потрібна окрема погоджена задача.

## Вкладення

Після створення draft wizard за потреби завантажує plotting або фото через
`POST /reports/{report_id}/media`. Файли зберігаються приватно поза БД і Git,
у gitignored storage; до `draft` допускаються upload/delete лише owner/admin.
Публічних URL для media немає.

## Перевірки та межі

Тести: pytest API/integration використовують SQLite у пам'яті; Node/jsdom
перевіряє frontend-модулі та DOM; Playwright має login, dashboard і wizard
flows із mock HTTP. Вони не замінюють реальний MariaDB E2E або повний
admin-review UI.

Перед public deployment ще потрібні public passport/QR, перевірений ML-контур,
PostgreSQL-portability та security hardening.
