# Розширення ринкових провайдерів і FX

## Мета

Розвинути foundation `0008_market_data_providers` без переписування historical
`StoneValuation`, demo `USD … d` чи public passport. NBU USD/UAH-частина
реалізована revision `0009_nbu_fx_snapshots`; майбутній provider потребує
окремого погодження.

## Передумови

- 110 реалізує OpenFacet adapter і ручний admin flow: candidate →
  approved/rejected → явне прикріплення `market_reference`.
- OpenFacet — лише model-based retail benchmark. Його дані не стають
  експертною, продажною чи транзакційною ціною.
- Поточна базова валюта OpenFacet — USD, unit — USD/ct. Курс НБУ не замінює
  ціну діаманта.

## Реалізовано

- `NBUStatService` USD endpoint читається лише сервером; network failure не
  підміняється старим курсом.
- Admin може вручну створити NBU snapshot на сторінці «Ринкові дані».
- Кожне прикріплення OpenFacet reference заново отримує NBU USD/UAH і в одній
  транзакції фіксує FX snapshot, Decimal rate, official rate date та UAH total.
- Підтримуваний новий або оновлений draft автоматично отримує immutable
  `system_market_reference` за останнім `approved` OpenFacet snapshot-ом і
  свіжим НБУ USD/UAH. Відсутність покриття або НБУ не блокує save; ідентичні
  market-входи не створюють дублікати.
- Admin може додати окремий `market_reference` з підтвердженням застосовності;
  він має пріоритет відображення над системним орієнтиром.
- Dashboard показує `d` для legacy demo, `*` для системного та `of` для
  підтвердженого OpenFacet; popover/detail пояснюють source, snapshot і frozen
  UAH. Passport та PDF цін не відкривають.

## Межі наступного рішення

1. Для кожного нового провайдера письмово зафіксувати ліцензію, право на
   зберігання/відображення, scope, API/формат, rate limits і expiry policy.
2. До scheduler погодити частоту, retry/backoff, timeout, observability,
   idempotency, ручний override і поведінку при недоступному джерелі.
4. Окремо погодити, чи можна показувати market reference у private report,
   public passport або PDF. За замовчуванням він залишається admin-only.
5. Додати adapter-specific unit/API tests із mock transport; integration tests
   не повинні залежати від зовнішнього мережевого API.

## Критерії готовності

- Нова міграція не редагує існуючі quotes чи valuations.
- Provenance, currency, unit, observation time і policy status доступні через
  API та UI.
- Є явні тести Decimal/rounding, provider failure й stale-data поведінки.
- Ліцензійні обмеження відображені в документації й UI там, де це потрібно.
