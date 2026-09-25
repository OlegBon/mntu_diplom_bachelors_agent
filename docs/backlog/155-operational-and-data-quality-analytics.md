# 155 — Розширення operational і data-quality analytics

## Мета

Доповнити наявну admin-only сторінку «Аналітика» корисними вимірюваними
показниками workflow та якості даних, не перетворюючи її на рейтинг людей,
ML-прогноз або приховане спостереження за публічними відвідувачами.

Provider operations і coverage виділені в 163 після multi-provider foundation
162, щоб не змішувати workflow/data-quality статистику з provider contract.

## Кандидати до реалізації

- **Workflow funnel:** створено → review → issued / повернено / void, кількість
  повторних повернень, тривалість до рішення та ageing поточної черги. Причини
  показувати лише у попередньо погоджених категоріях, не як raw private texts.
- **Якість report data:** coverage обов'язкових і необов'язкових полів,
  розподіли shape/4C/origin/treatment, completeness geometry, медіа та
  publication readiness. Це опис набору, не оцінка експерта.
- **Публічний delivery workflow:** частота publish/revoke/reissue та PDF/media
  readiness на рівні report. Не збирати analytics про anonymous visitors,
  QR-scans або персональні дані без окремої privacy/product задачі.
- **Тексти:** metadata-only words/chars/min/max належать 154 і не дублюються
  тут як score.

## Правила

- Кожна метрика визначає population, date source, denominator, null policy і
  чи вона бере current state або append-only event.
- Admin-only; агрегати, а не непотрібне відкриття приватних коментарів.
- Відображати empty, partial-data та historical-limit states; не вигадувати
  backfill для даних, яких у подіях немає.

## Поза межами

- Performance ranking експертів, content sentiment/truth scoring, ML/SOM,
  price accuracy claims, tracking відвідувачів або public analytics.
