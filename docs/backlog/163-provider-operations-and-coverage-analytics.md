# 163 — Аналітика operations і coverage provider-ів

## Мета

Додати admin-only tab «Провайдери», щоб бачити якість роботи інтеграцій та
покриття ринковими орієнтирами без оцінювання provider-а як «правильного» і
без публічної аналітики.

## Залежності

122 (scheduler/operation log), 162 (multi-provider policy/valuations) і 155
(спільні правила operational/data-quality analytics).

## Scope

- Freshness останнього snapshot-а, configured warn/block thresholds,
  scheduled/manual outcomes, retry, candidate → approved/rejected і причина.
- Coverage нових або змінених operational drafts за provider-ом; причини
  непокриття (scope, origin, shape, 4C, carat, stale/missing snapshot).
- Counts provider-specific system/manual valuations, period filtering і links
  лише до private admin reports, коли це дозволено RBAC.
- Нейтральне side-by-side відображення availability кількох provider-ів без
  average, accuracy score, investment conclusion або public tracking.

## Перевірки

Admin-only API/UI, period/filter correctness, empty/error states, provider без
snapshot-а, coverage=0, excluded demo/operational scope за контрактом та
desktop/mobile accessibility.

## Поза межами

Новий provider adapter, зміна policy, public/PDF display, ML/SOM або
економічне порівняння цін різних provider-ів.
