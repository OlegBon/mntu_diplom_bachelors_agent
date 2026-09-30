# 176 — i18n private report workflow

## Мета

Повністю локалізувати private report surfaces: dashboard, report wizard,
private detail/edit, lifecycle, report filters і dialogs.

## Передумови

- 175 — i18n core і shared shell.
- 146 — versioned wizard draft continuity.

## Scope

- Static Pug і dynamic JS messages private report workflow переводяться на
  catalog keys та centralized formatters.
- Domain codes/values отримують presentation labels без зміни API/DB.
- Browser E2E доводить, що перемикання locale під час wizard і detail edit не
  губить form values, active step, report ID або filter query state.
- Expert-authored comment, conclusion і lifecycle reason лишаються точним
  оригінальним текстом незалежно від locale.

## Поза межами

- Admin/demo/analytics surfaces, public passport/PDF і machine translation.

## Критерії готовності

- Кожний видимий control, status і validation message у scoped flow має повні
  `en`/`uk` catalog values.
- E2E покриває switch на draft/edit без server write, hidden draft або reload.
