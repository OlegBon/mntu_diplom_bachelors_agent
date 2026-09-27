# Synthetic demo provider analytics

## Призначення

Вкладка **Демо → Провайдери** показує лише coverage та provenance двох
вигаданих джерел — `Demo Market A` і `Demo Market B`. Це read-only спосіб
перевірити multi-source UX без читання OpenFacet, IDEX, provider snapshots,
операцій, логотипів чи реальних ринкових значень.

Суми — immutable `synthetic_demo_reference` у USD для всього каменю. Вони не
є market value, прогнозом, ціною продажу, оцінкою точності чи рейтингом
провайдера.

## Один механізм для demo та майбутніх real data

`backend/provider_analytics.py` містить спільний read-only агрегатор. Він
приймає server-defined `ProviderAnalyticsScope`:

- `record_scope` і, за потреби, конкретний `dataset_id`;
- допустимі `valuation_kind`;
- allow-list назв provider-ів.

Demo adapter передає тільки scope `demo`, поточний immutable manifest,
`synthetic_demo_reference` та `Demo Market A/B`. Жоден URL, report ID або
frontend прапорець не може розширити цей набір.

Для real data механізм може бути використано тим самим adapter contract лише
після окремого policy/permission gate: письмових умов провайдера, дозволеного
типу аналізу, визначеного набору immutable valuation і достатнього quality
контексту. До цього real adapter та його UI/API не активуються. OpenFacet/IDEX
не є fallback для demo і не стають analytics/training data через сам факт
наявності runtime reference.

## Доступ і зріз

Маршрут `GET /demo/datasets/{dataset_id}/provider-analytics` доступний тільки
admin-у з увімкненим demo opt-in; для інших користувачів та неавторизованих
він використовує той самий opaque `404` gate, що й інші `/demo/*` маршрути.

Manifest повинен містити explicit scenario `demo_provider_analytics`. Revision
`0020_demo_provider_analytics_eligibility` додає його тільки до відомих
`synthetic-demo-v*` manifests. Вона не змінює reports, stones, valuations,
SOM artifacts чи operational records.

Фільтр дат спільний із вкладками demo workflow. Межі інклюзивні та
відбирають demo reports за `report_date`; далі агрегуються лише valuation,
прив'язані до каменів цих звітів. Таблиця показує покриття, кількість значень,
діапазон дат observation, медіану, діапазон і read-only посилання на останній
demo report. Назва provider-а клікабельна: модалка показує серверно задані
source class, provenance, статус умов і policy використання. Для demo статус
прямо каже, що це не договір, ліцензія або дозвіл на real provider data.

## Межі

- Сервіс не читає `market_data_providers`, snapshots, schedules або
  operations — це окрема задача 163.
- Він не створює й не оновлює жодних записів.
- Він не використовує `DiamondReport.price`, не конвертує валюту та не робить
  порівняння якості provider-ів.
- SOM використовує свій окремий policy scenario й immutable artifact; provider
  analytics не змінює ані карту, ані її assignment.

Пов'язані документи: [ізоляція demo dataset](../decisions/006-demo-dataset-isolation.md),
[multi-provider reference contract](../decisions/007-multi-provider-market-references.md),
[synthetic SOM](./synthetic-som-demo.md) та [guide market provider-ів](./market-data-providers.md).
