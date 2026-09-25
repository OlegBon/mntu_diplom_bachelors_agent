# Провайдери ринкових даних і системний орієнтир

## Межа термінів

Системний довідковий орієнтир — це відтворювана private-величина для
підтримуваного каменю. Він не є експертною оцінкою, ціною пропозиції,
транзакційною чи продажною ціною. Public passport і PDF не містять таких сум.

`diamond_market.market_price_reference` — legacy demo-індекс. Він не є
каталогом провайдерів і не керує новими звітами.

## Три різні записи

| Об’єкт | Призначення | Змінюється? |
| --- | --- | --- |
| `market_data_providers` | Каталог доступних джерел та їхніх умов | Так, лише admin і окремий provider flow. |
| `market_reference_policies`, `market_reference_policy_providers` | Одна policy з enabled set та nullable primary для **майбутніх** системних орієнтирів | Так, лише admin. |
| `market_data_snapshots`, `fx_data_snapshots`, `stone_valuations` | Конкретні отримані дані й суми звіту | Ні, immutable. |
| `market_provider_schedules`, `market_provider_operations` | Графік, freshness-пороги та журнал спроб отримання | Графік змінює admin; журнал append-only. |

## Налаштування admin

На сторінці «Ринкові дані» admin:

1. Увімкнює checkbox-ами один або кілька провайдерів майбутнього системного
   орієнтиру та, за потреби, обирає одного **Основним для списку звітів**.
   Primary має входити до enabled set; `NULL` не показує одну суму за
   замовчуванням. Зараз фактично підтриманий лише OpenFacet; новий провайдер
   спершу має бути зареєстрований у каталозі та мати server adapter.
2. За потреби вмикає checkbox «Додавати еквівалент у UAH». Для поточної policy
   це означає НБУ USD/UAH.
3. Зберігає policy. Вона не змінює вже створені або видані звіти.
4. Отримує candidate даних кожного потрібного провайдера, перевіряє та approve його окремо.
5. У блоці «Автоматичне оновлення» задає час у `Europe/Kyiv`, увімкнення та пороги warning/block. Початкові значення: OpenFacet — 08:30, НБУ — 15:40; повторні спроби після помилки — 15, 30 і 60 хвилин.

## Операційне оновлення

FastAPI не запускає фоновий цикл самостійно. Hosting або Windows Task Scheduler викликає
`python scripts/run_market_provider_schedule.py` у потрібний інтервал (наприклад, кожні 5 хвилин).
Команда сама визначає, чи настав час конкретного provider-а, записує кожну спробу в
`market_provider_operations` і є безпечною при повторному запуску. OpenFacet за графіком створює
лише immutable `candidate`; approve завжди лишається окремим рішенням admin. НБУ зберігає
новий immutable snapshot або фіксує `no_change` для того самого курсу й official date.

Під час `POST /reports`, `PUT /reports/{id}` та ручного attach зовнішній HTTP-запит **не** виконується.
Коли UAH увімкнено, server використовує останній вже збережений NBU snapshot тільки якщо він не
перевищив `block_after_hours`. Якщо snapshot відсутній або застарілий, draft не ламається і
системний орієнтир не додається; ручний attach повертає контрольовану помилку з вимогою оновити НБУ.
Збережені valuation, historical report, public passport і PDF не перераховуються.

У `0015_multi_provider_market_references` локальна policy переносить
`openfacet` у enabled set і dashboard primary, а `nbu` лишається FX-провайдером
з увімкненою UAH-конвертацією. Це відтворює попередню поведінку без backfill.

## Що відбувається зі звітом

У майстрі до збереження `POST /reports/preview` використовує ту саму policy та
останній `approved` snapshot, щоб показати можливий USD-орієнтир. Це лише
preview: він не створює valuation і не отримує НБУ. Після збереження server
повторює розрахунок для фактичних даних чернетки та фіксує результат.

Під час створення нового або збереження зміненого `draft` backend читає policy:

1. для кожного enabled provider бере його останній `approved` snapshot;
2. перевіряє його покриття для natural stone, shape, color, clarity та carat;
3. незалежно обчислює total USD і фіксує provider-specific `system_market_reference`;
4. якщо policy увімкнула FX, отримує свіжий НБУ USD/UAH і фіксує UAH разом зі
   snapshot-ом курсу.

Відсутній approved snapshot, непідтримуваний камінь або тимчасово недоступний
НБУ не заважають зберегти draft: просто не створюється новий системний
орієнтир. Однакові snapshot та market-входи не створюють дублів.

Admin може окремо прикріпити `market_reference` з поясненням застосовності.
Такий ручний запис має пріоритет у dashboard, але не перетворює суму на
експертну оцінку.

Коли server створює новий `system_market_reference`, або admin створює
ручний `market_reference`, private «Історія змін» звіту отримує окрему
append-only подію із сумою, провайдером і номером snapshot-а. Ідемпотентне
повторне збереження без нового valuation події не додає.

## Відображення

У «Всі звіти» колонка `Ціна (USD)` містить лише суму обраного primary provider,
його незалежний тип і джерело: `SYS · OpenFacet` для системного орієнтиру або
`ADM · OpenFacet` для provider-specific ручного підтвердження. Якщо існують інші
орієнтири, `+N` відкриває доступний список у popover. Якщо primary не має
покриття, інше значення не підставляється приховано. Private detail показує
окремі cards, snapshot і зафіксований НБУ-еквівалент кожного запису.

Логотип provider-а, якщо з'явиться, зберігається тільки як локальний vetted
`brand_asset_key`; remote URL не використовується. Логотип IDEX не додається до
письмового дозволу IDEX. Public passport і PDF не показують provider values чи
брендинг без окремого рішення про disclosure/licensing.

## Розширення

Новий провайдер потребує окремого adapter-а, перевірки ліцензій, coverage,
валюти, unit, rate limits і тестів. Лише після цього він з’являється в каталозі
й у checkbox-наборі policy. Новий FX-провайдер також потребує server fetcher:
сама конфігурація не дозволяє підміняти НБУ невідомим джерелом.

## Межа аналітичного використання OpenFacet

OpenFacet snapshots не є ціною продажу, transaction data, експертною оцінкою
або автоматично дозволеним ML dataset. За чинними
[OpenFacet Terms of Use](https://openfacet.net/en/terms/) (перевірено
2026-09-24) public information може використовуватися для research та ordinary
internal business purposes за коректної атрибуції. Це допускає окремий
admin-only descriptive analysis на versioned snapshots у фактичному supported
natural GIA scope.

Такий analysis не може перевидавати substantial raw data, бути customer-facing
або потрапляти у public passport/PDF без окремої ліцензії. Він показує provider,
Terms URL/date, snapshot timestamp/version і disclaimer про model-based retail
benchmark. Перед retention, новим автоматизованим використанням або зміною
призначення потрібно повторно перевіряти Terms: OpenFacet може змінити,
обмежити чи припинити API access. Verified ML, training labels і будь-яка
аналітика IDEX потребують окремого письмового дозволу.
