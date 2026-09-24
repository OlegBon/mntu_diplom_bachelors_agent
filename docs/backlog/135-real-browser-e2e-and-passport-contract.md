# 135 — Реальний browser E2E і контракт публічного паспорта

## Мета

Зробити browser-перевірки release-надійними: виправити застарілий mock
контракт private passport UI та спроєктувати ізольований реальний E2E flow
з API і MariaDB без використання робочих облікових записів або даних.

## Підтверджений стан

24 вересня 2026 повний Playwright набір має 16/17. Тест
`public-passport-delivery.spec.mjs` мокав raw passport, тоді як чинний
`GET /reports/{id}/passport` повертає wrapper `{ "passport": ... }` (і
`{ "passport": null }` для нормального unpublished state). Через це UI
правильно залишає code hidden, а тест помилково очікує його показ.

## Scope

- Оновити mock/contract assertion публічного passport delivery без зміни
  production behavior.
- Покрити published, unpublished, revoked і void межі, QR/PDF/media
  allow-list та 404 public token-а.
- Визначити окрему test-auth стратегію: disposable DB/schema, test users,
  isolated storage та cleanup без `seed_db.py` проти робочої MariaDB.
- Додати один реальний browser flow login → dashboard → wizard → draft →
  review → issue → passport/PDF та зафіксувати команду в runbook.

## Поза межами

- Використання локальних робочих облікових даних у Playwright.
- Зміна lifecycle, public projection або генерації PDF лише задля тесту.

## Критерії готовності

- Повний Playwright набір стабільно проходить.
- Реальний flow працює проти ізольованого test runtime, а не mock-only API.
- Негативні public/RBAC scenarios не розкривають приватні дані.
