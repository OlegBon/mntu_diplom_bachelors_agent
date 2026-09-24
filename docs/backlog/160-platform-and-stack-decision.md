# 160 — Platform і stack decision для staging

## Мета

Підтвердити практичний cloud-contour після локально перевіреного ML, без
передчасного frontend rewrite.

## Передумова

Спершу погоджується [ADR-005](../decisions/005-analytics-and-verified-ml-strategy.md):
cloud не є передумовою локального data/ML етапу. Якщо 151/152 підтвердять
працездатний verified experiment, він лишається локально відтворюваним до
вибору staging-платформи.

## Погоджений baseline

- Залишаємо FastAPI/Python: він придатний для domain logic, provider adapters і
  майбутніх ML-бібліотек.
- Залишаємо Gulp + Pug + vanilla JavaScript для staging/першого production.
  Static frontend може віддаватися з CDN, Docker або static hosting.
- PHP/shared-hosting rewrite не розглядається.
- Vite або TypeScript не є обов'язковими. Повернення до Vite можливе окремо як
  MPA build migration, якщо TypeScript/HMR/dependency complexity дасть
  вимірювану користь; Next/React — лише за конкретною потребою SSR/SEO або
  складної component architecture.

## Scope

- ADR: FastAPI + static frontend deployment topology, managed PostgreSQL,
  secrets, costs/limits, backups, logs, domains/TLS і rollback.
- Порівняти cloud options на дату рішення лише за офіційними умовами; не
  прив'язувати architecture до мінливого free tier.
- Визначити критерії для поступового TypeScript/Vite, не змішуючи їх із 161.
