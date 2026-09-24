# 145 — Контракт мультимовності

## Мета

Спроєктувати English-first (`en`) та Ukrainian (`uk`) presentation layer без
зміни доменних даних, lifecycle або незбереженого введення.

## Погоджені правила

- Default locale — English; перемикач підтримує `en` і `uk` та лишає користувача
  на тій самій сторінці з тими самими query-параметрами/report ID.
- Locale є presentation-only: не змінює codes, permissions, status, IDC results,
  dates/numbers у БД або API-значення.
- Перемикання в wizard/detail edit не очищує незбережені form values; авторські
  comment/conclusion/reason не перекладаються автоматично.
- QR/token не залежать від мови; public page може мати locale у URL без зміни
  public ID. PDF потребує явного validated locale parameter.

## Залежність

- До реалізації необхідна [146 — незбережене введення майстра](./146-wizard-draft-continuity.md):
  саме вона дає browser-state для безпечного locale switch, reload і
  повернення на сторінку. I18n не створює hidden server draft.

## Декомпозиція перед реалізацією

- Translation catalog, fallback, formatting dates/numbers/currency, server labels,
  public passport/PDF, DOM/E2E locale tests і accessibility.
- Визначити, чи робити поступовий TypeScript разом із i18n лише після 160.

## Поза межами

- Машинний переклад приватних або експертних текстів.
- Переклад уже збережених даних чи зміна ruleset-ів.
