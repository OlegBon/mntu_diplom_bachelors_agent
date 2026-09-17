# Розширення ринкових провайдерів і FX

## Мета

Розвинути foundation `0008_market_data_providers` лише після юридично й
продуктово погодженого джерела. Додати валютний курс або нового провайдера без
переписування historical `StoneValuation`, demo `USD … d` чи public passport.

## Передумови

- 110 реалізує OpenFacet adapter і ручний admin flow: candidate →
  approved/rejected → явне прикріплення `market_reference`.
- OpenFacet — лише model-based retail benchmark. Його дані не стають
  експертною, продажною чи транзакційною ціною.
- Поточна базова валюта OpenFacet — USD, unit — USD/ct. Курс НБУ не замінює
  ціну діаманта.

## Межі наступного рішення

1. Для кожного нового провайдера письмово зафіксувати ліцензію, право на
   зберігання/відображення, scope, API/формат, rate limits і expiry policy.
2. Якщо потрібна UAH-проєкція, окремо versionувати NBU USD/UAH snapshot з
   датою, timezone, unit, exact Decimal rounding і посиланням на конкретний
   market snapshot. Новий FX snapshot не змінює старі результати.
3. До scheduler погодити частоту, retry/backoff, timeout, observability,
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
