# 157 — Детермінований generator synthetic demo dataset

## Мета

Створити відтворюваний admin-only `synthetic-demo-v1` із достатніми,
узгодженими полями для демонстрації report UI і SOM, без реальних даних.

## Scope

- Окремий non-destructive generator/loader, не `seed_db.py`; explicit target
  scope, deterministic random seed, checksum, manifest і idempotent rerun.
- Працювати лише після рішення 156 про system-origin для assets/events:
  generator не може привласнювати demo-активність реальному обліковому запису.
- Нові `DEMO-…` reports мають повний normalized `Stone`, issued/read-only
  lifecycle, synthetic author/provenance, expert/system grades, text samples
  без персональних даних та `synthetic_demo_reference` із чіткою одиницею.
- Synthetic `issued` є лише станом внутрішньої демонстрації: generator не
  створює `PublicPassport`, QR або публічний URL.
- Використовувати synthetic або підтверджено ліцензовані media. Зображення
  потрібні лише для невеликого showcase subset; числова популяція для SOM не
  потребує тисячі дубльованих файлів.
- Генератор не викликає OpenFacet, НБУ, IDEX, public routes або scheduler; не
  пише у existing operational rows і не використовує реальні тексти/файли.

## Критерії даних

- Явні розподіли natural/lab-grown/other, shape, 4C, geometry, treatment,
  status і synthetic price reference; no impossible geometry by generator rules.
- Dataset card описує, що це synthetic development demo, а не ринковий набір,
  training data, sale history чи інвестиційна рекомендація.

## Перевірки

Повторний запуск не створює дублів; checksum/count/ID range збігаються;
генератор не виконує network I/O; selected demo report має заповнені поля та
ліцензійно безпечні assets.
