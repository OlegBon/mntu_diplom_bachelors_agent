# 179 — i18n runtime completion audit

## Мета

Завершити локалізацію вже реалізованих private, admin та synthetic Demo
поверхонь, де після 177 залишилися runtime-підписи, fallback-стани або
табличні значення поза `en`/`uk` catalog.

## Передумови

- 175 — i18n core і shared shell.
- 176 — private report workflow.
- 177 — admin, Demo та Analytics surfaces.

## Scope

- Demo: tabs, cards, dialogs, таблиці, filters, loading/error/empty states і
  runtime-поля для stones, experts, texts, operations/quality,
  administrators, providers та currency sources.
- Market data і всі Analytics tabs: static та runtime labels, action/status
  copy, dialogs, fallback states і locale-change rendering.
- Private dashboard/report detail: залишкові presentation labels та
  locale-change rendering без перекладу авторських висновків, коментарів,
  reasons або domain data.
- Перевірка catalog coverage для user-visible runtime text і цільові browser
  regression scenarios в обох locales.

## Поза межами

- Privacy/Documentation pages, public passport та PDF renderer — 178.
- API content negotiation, переклад response payloads, historical data rewrite,
  TypeScript/Vite або translation service.
- Формат native `input[type=date]`: його calendar UI і placeholder контролює
  браузер/операційна система, а не catalog застосунку.

## Критерії готовності

- У scoped screens немає змішаного presentation copy у static, dynamic,
  loading, empty, error і dialog states.
- Перемикання locale перестворює або оновлює dynamic controls без втрати
  route/query/hash, form state, RBAC чи demo isolation.
- `en` і `uk` catalogs мають повну key parity; frontend unit, full mock E2E та
  relevant real isolated flow проходять локально й у GitHub Actions.
