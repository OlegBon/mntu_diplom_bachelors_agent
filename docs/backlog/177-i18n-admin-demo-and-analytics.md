# 177 — i18n admin, demo та analytics surfaces

## Мета

Повністю локалізувати authenticated admin, synthetic demo і analytics UI,
зберігаючи policy, provider та synthetic-scope межі.

## Передумови

- 175 — i18n core і shared shell.
- 176 — private workflow establishes dynamic rendering pattern.

## Scope

- Experts, profile, references, market data, demo reports/detail і analytics
  переходять на catalog keys/formatters.
- Provider codes, dataset IDs, record scope, immutable provenance, roles та
  status values не змінюються; перекладаються лише їхні presentation labels.
- Admin/demo browser checks у двох locale перевіряють, що locale switch не
  обходить RBAC/demo access і не змінює filter/report URL state.

## Поза межами

- Public passport/PDF locale renderer, API-localized data та TypeScript.

## Критерії готовності

- Scoped admin/demo/analytics screens не мають змішаних user-visible locale.
- Restricted provider/demo policy і synthetic disclaimers лишаються змістовно
  тотожними в обох мовах.
