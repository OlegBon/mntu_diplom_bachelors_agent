# 175 — i18n core і спільна оболонка

## Мета

Реалізувати frontend locale runtime за ADR-008 та повністю локалізувати shared
shell: header, navigation, session/retry state, footer, login і landing.

## Scope

- Catalog loader/validator, `t()` та централізовані `Intl` formatters без
  сторонньої бібліотеки або TypeScript.
- `en` default, `uk` option, precedence URL/preference/default, `?lang=`
  synchronization без reload і без втрати інших URL state.
- Locale switcher, `html[lang]`, title та доступні labels у common layout.
- Повні `en`/`uk` рядки для login, landing і shared shell; dynamic auth/nav
  labels також використовують catalog.
- Catalog parity, locale state та public/login DOM/browser tests.

## Поза межами

- Private report workflow, admin/demo/analytics screens і public PDF.
- Locale-dependent API responses або переклад user-authored text.

## Критерії готовності

- Перемикач не перезавантажує сторінку, не змінює route/hash/наявні query
  parameters і має доступну назву поточної/альтернативної мови.
- У scoped surfaces немає user-visible hardcoded `en`/`uk` строк поза
  catalog; parity test гарантує обидва переклади кожного release key.
- Login і public passport lookup працюють в обох locale без зміни API payload.
