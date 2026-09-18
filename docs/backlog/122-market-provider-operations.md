# 122 — Операційний контур ринкових провайдерів

## Мета

Погодити та реалізувати кероване оновлення даних market provider-ів після
завершення 110/121: freshness policy, scheduler та безпечне підключення нового
провайдера без переписування historical `StoneValuation`, legacy `USD … d` чи
public passport.

## Передумови

- OpenFacet має immutable candidate/approved/rejected snapshots; NBU USD/UAH
  фіксується разом із новим reference.
- Admin уже обирає одного market provider-а та вмикає/вимикає UAH-конвертацію
  лише для майбутніх системних орієнтирів.
- Поточний ручний flow не має scheduler-а: snapshot-и створюються свідомо
  адміністратором, а відсутність покриття чи недоступність джерела не блокує
  збереження чернетки.

## Scope

- Для кожного нового market або FX provider-а зафіксувати ліцензію, право на
  зберігання та відображення, scope, API/формат, rate limits і expiry policy.
- Спроєктувати scheduler: частоту, timezone, timeout, retry/backoff,
  observability, idempotency, ручний override і поведінку за недоступного
  джерела.
- Визначити freshness policy: коли snapshot позначається застарілим, що бачить
  admin і чи дозволене автоматичне створення системного орієнтиру за таким
  snapshot-ом.
- Для нового adapter-а додати ізольовані unit/API тести з mock transport;
  integration-тести не мають залежати від зовнішнього API.
- Окремо погодити, чи може ринковий орієнтир з’явитися у public passport або
  PDF. До такого рішення він лишається private.

## Поза межами

- Backfill або переоцінка існуючих `StoneValuation`.
- Перетворення OpenFacet reference на експертну, продажну чи транзакційну ціну.
- Заміна legacy `DiamondReport.price` або demo-позначки `d`.
- Власне підключення конкретного комерційного провайдера без окремо погоджених
  умов використання.

## Відкриті рішення

- Чи потрібен scheduler у локальному MVP, чи достатньо ручного refresh до
  появи production-контуру?
- Які максимальний вік snapshot-а й UX-попередження є прийнятними для OpenFacet
  та НБУ?
- Чи потрібні різні policy для різних типів каменів або market use cases?
- Який канал observability використовуватиметься поза локальною розробкою?

## Критерії готовності

- Оновлення не змінює historical quotes, FX snapshots, valuations або
  report-event history.
- Кожен provider має documented scope, ліцензійні межі, API contract та тестове
  покриття failure/stale-data сценаріїв.
- Scheduler, якщо погоджений, є ідемпотентним, має ручний override та не
  робить неконтрольованих зовнішніх запитів під час save звіту.
- У `docs/progress.md` зафіксовано рішення, перевірки й обмеження.
