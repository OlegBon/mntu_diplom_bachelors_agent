# 164 — Synthetic demo actors і workflow analytics

## Мета

Додати до `synthetic-demo-vN` правдоподібний, але повністю ізольований зріз
віртуальних експертів і адміністраторів для внутрішньої демонстрації workflow
та статистики. Він не створює облікових записів, не змінює RBAC і не змішує
демо-активність із операційними показниками.

## Scope

- Окрема deterministic metadata-модель synthetic actors: стабільний ID,
  display name/role, dataset version і лише згенеровані non-PII атрибути.
  Реальні `experts` і JWT-користувачі не використовуються.
- Явне, відтворюване призначення demo-звітів, status events і workflow
  timestamps synthetic actors. Жоден operational report/event не переписується.
- Вкладки «Експерти» та «Адміністратори» у розділі «Демо»: спільний зріз
  `від / до / за весь час`, loading/empty/error states, прозора методологія та
  read-only drill-down у demo reports.
- Метрики обмежені демонстраційним workflow: кількість звітів і статусів,
  завершені synthetic intervals, completeness. Не показувати реальну
  продуктивність людей, рейтинг, SLA або висновки про якість експерта.
- Операції generator/reseed мають лишатися explicit local development action;
  документуються idempotency, checksum, безпечний reset і те, що зміна
  генератора створює нову версію dataset, а не переписує поточну.

## Перевірки

Однаковий generator input дає ті самі actors/assignments; admin бачить лише
synthetic зріз, expert/anonymous отримують `404`; реальні accounts, operational
reports і operational analytics не змінюються; date slice не дає даних поза
межами та не покладається лише на колір у UI.

## Залежності

156, 157 і завершена 158. Може потребувати окремої Alembic revision та
окремого підтвердження її застосування до локальної БД.
