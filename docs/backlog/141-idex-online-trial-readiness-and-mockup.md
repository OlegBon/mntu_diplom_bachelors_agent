# 141 — IDEX Online: підготовка trial і англомовний mock-up

## Мета

Підготувати безпечний, ліцензійно прозорий старт погодженого IDEX Online
30-day complimentary non-production trial після готовності staging.

## Погоджені умови

- Лише natural diamonds; до 10 low-volume market-reference requests/day,
  орієнтовно 100/month.
- Лише internal development/test records: без trading, inventory search,
  redistribution або customer-facing distribution.
- Sanitised mock-up можна підготувати локально; trial стартує лише після
  завершення local verified ML за [150](./150-analytics-and-verified-ml-strategy.md),
  готового staging за [161](./161-postgresql-migration-and-staging.md) та
  повідомлення IDEX із запропонованою датою.
- IDEX Online має бути явно названий джерелом; natural-only wording і межа
  «not an appraisal, transaction price or offer» потрібні завжди.

## Scope

- Sanitised English sample report/mock-up з ілюстративною, не IDEX-сумою.
- Поруч із value зарезервувати місце для credit і потенційного IDEX Online logo.
- Не використовувати logo у фактичному UI/PDF, доки IDEX письмово не підтвердить
  display/branding requirements.
- Описати provider adapter contract: API key тільки через env, rate limit,
  source timestamp/unit/currency/terms, immutable snapshots і provenance.
- Переконатися, що save report не викликає IDEX напряму, а data не виходять за
  узгоджений private scope.

## Поза межами

- Реальний key, activation або network integration до готового staging.
- Lab-grown data, commercial licence, public/PDF distribution і придбання даних.
