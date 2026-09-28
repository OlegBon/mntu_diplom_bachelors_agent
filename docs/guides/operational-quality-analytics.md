# Operational і data-quality analytics

«Аналітика → Операції та якість» — admin-only read model для опису поточного
workflow та повноти operational звітів. Вона не оцінює людей, не аналізує зміст
коментарів, не створює rating і не відстежує відвідувачів публічного паспорта.

## Що показує

| Блок | Що вимірює | Джерело дати / population |
| --- | --- | --- |
| Workflow | Створення, review, повернення, видачу, анулювання, повторні повернення | `ReportEvent.created_at` у вибраному періоді, лише `record_scope=operational` |
| Поточний стан когорти | Current status звітів, створених у зрізі | `DiamondReport.created_at` у вибраному періоді |
| Поточна черга | Усі operational звіти у `review`, найдавніший review event | Current state, без історичного фільтра |
| Поля | Заповнені/відсутні обов’язкові й додаткові поля | Когорта за `created_at` |
| Delivery | Private media, active public passport, видані без active passport | Когорта за `created_at` |

Числа в різних блоках не потрібно механічно прирівнювати: workflow у травні
може належати звіту, створеному раніше, тоді як status когорта травня містить
лише звіти, створені у травні.

## Контракт API

```
GET /statistics/operational-quality?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
Authorization: Bearer <admin JWT>
```

Параметри необов’язкові та включні для календарного дня. Без них відповідь
охоплює весь доступний operational період. Не-admin отримує `403`,
неавторизований запит — `401`.

Відповідь навмисне агрегована: `report_cohort_count`, статуси, event counts і
`{key, applicable_count, filled_count, missing_count}` для покриття. Вона не
містить `expert_comment`, reasons переходів, уривків або visitor data.

## Null policy

- `geometry` заповнена лише коли існують table, depth, crown angle і pavilion
  angle; кожне інше поле має власний independent denominator.
- Додаткові origin/treatment поля не вважаються заповненими для `unknown` та
  `not_assessed`; текстові поля нормалізують whitespace.
- `issued_without_active_passport_count` не означає помилку: passport — окрема
  добровільна delivery-дія.
- За порожньої когорти всі лічильники дорівнюють нулю: historical backfill не
  вигадується.

## Межі та код

Контур не дублює «Тексти» (там лише metadata lengths/empty links) і не включає
SOM, benchmark, ціну, forecast чи investment category. Provider freshness має
окремий date source у вкладці «Провайдери».

`backend/main.py` захищає route через `require_admin`; агрегація живе у
`backend/crud.py:get_operational_quality_analytics`, response contract — у
`OperationalQualityAnalyticsResponse`. Frontend використовує лише цей
агрегований API через `getOperationalQualityAnalytics`.
