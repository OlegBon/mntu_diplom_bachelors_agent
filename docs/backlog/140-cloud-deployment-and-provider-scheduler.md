# 140 — Хмарне розгортання та scheduler ринкових даних

## Мета

Розгорнути Diamant ID у staging/production та підключити керований scheduler
обраного хмарного середовища для `scripts/run_market_provider_schedule.py`.

## Передумови

- `0013_market_provider_operations` уже має графіки OpenFacet/НБУ, freshness-пороги,
  retries 15/30/60 хвилин і append-only журнал операцій.
- Скрипт не є daemon-ом: один запуск безпечно перевіряє, чи є provider простроченим,
  і не виконує зайвий fetch.
- Локальний Windows Task Scheduler навмисно не налаштовується: він залежить від
  увімкненого ПК та не є production-contour.
- Спершу має бути виконано platform decision у [160](./160-platform-and-stack-decision.md)
  та створено staging за [161](./161-postgresql-migration-and-staging.md).

## Scope

- Обрати cloud/staging runtime, домен, TLS, секрети та MariaDB/PostgreSQL strategy.
- Налаштувати managed cron/scheduled job кожні 5 хвилин з робочою папкою проєкту й
  командою `python scripts/run_market_provider_schedule.py`.
- Перевірити timezone `Europe/Kyiv`, один активний scheduler, timeout, вихідний код,
  logs і alert на серію невдалих спроб.
- Перевірити, що job має доступ лише до необхідних env/DB та не створює report,
  не approve OpenFacet candidate і не переписує historical valuation.
- Описати runbook: ручний запуск, перегляд `market_provider_operations`, пауза
  provider-а, відновлення після downtime та rollback deployment.

## Поза межами

- Локальна Windows Task Scheduler задача.
- Новий комерційний market provider, його API key чи ліцензійна інтеграція.
- Автоматичне approve candidate, backfill/reprice, public passport/PDF ціни.

## Критерії готовності

- Cloud scheduler виконує лише due jobs і фіксує результат у журналі.
- Повторний запуск не дублює snapshot або valuation.
- НБУ і OpenFacet працюють за policy; failure не блокує save draft.
- Є staging smoke-check і documented production runbook.
