# 151 — Контракт даних і якість для stone analytics

## Мета

Визначити легальний, відтворюваний dataset для експериментів ціни та
кластеризації до написання ML-коду.

Synthetic demo за 156–159 є окремим technical population і не задовольняє
критерії цього завдання для verified ML або real-world SOM.

## Обов'язкові рішення

- Розділити data tiers у manifest: synthetic project seed
  `DR-00001`–`DR-01000`, private reports після `DR-01000` і кожне зовнішнє
  джерело. Їх не об'єднувати за замовчуванням. Seed дозволений лише для
  технічного demo/experiment, не як verified market label.
- Для private reports після `DR-01000` зафіксувати owner, legal/purpose basis,
  consent за потреби, retention, доступ і de-identification до будь-якого
  ML/SOM використання. Відсутність такої картки означає exclude by default.
- Зафіксувати письмову ліцензію, owner, дозволені training/derivative uses,
  retention і атрибуцію кожного джерела. OpenFacet та майбутній IDEX не є
  training dataset, доки відповідний дозвіл прямо не отримано. Виняток лише
  для окремої descriptive internal OpenFacet-аналітики: Terms review,
  `terms_url`/date, snapshot provenance, source scope, attribution і заборона
  public/raw redistribution мають бути зафіксовані в dataset card.
- Визначити окремі population: natural і lab-grown не змішуються без
  обґрунтованої моделі та даних. Оброблені/невідомі камені мають явне правило
  включення або виключення.
- Визначити target: для першого експерименту — ліцензована нормалізована
  USD/ct reference або фактична sale price, якщо такий provenance існує.
  Asking/list price, provider reference і realised sale price не є одним
  target і не можуть непомітно замінювати одне одного.
- Описати feature contract, units, currency/date normalization, source
  timestamps, missing/outlier policy, duplicate/leakage checks і quality report.
- Вести versioned provider-policy card для кожного зовнішнього джерела:
  agreement/Terms evidence, owner, дозволені purposes (`reference_display`,
  `aggregate_analytics`, `descriptive_clustering`, `model_training`, export),
  field scope, attribution, retention, effective/expiry/review dates і статус.
  Застосунок не інтерпретує юридичний текст автоматично: відповідальний admin
  фіксує перевірене рішення, а server-side policy gate виконує його технічно.
- Policy застосовується до **окремого значення**, а не лише до всього каменю.
  Для кожного feature з provider provenance experiment має мати явний,
  versioned selection rule. Заборонене або прострочене значення не потрапляє у
  feature vector, нормалізацію, SOM/model artifact чи explanation. Камінь
  лишається допустимим, якщо всі обов'язкові features можна сформувати з інших
  дозволених джерел; інакше виключається саме з цього запуску з причиною.
  Один камінь може з'явитися в experiment лише раз — ніколи по одному разу на
  кожного provider-а. Mixed-source manifest зберігає policy version і
  per-feature provenance для кожного використаного значення.
- Quality report показує candidate/accepted/excluded population, причини
  виключення та coverage дозволених provider values. Спливання або відкликання
  policy блокує новий запуск; старий artifact зберігає audit provenance і
  відображається лише відповідно до policy.
- Зафіксувати versioned immutable dataset manifest, reproducible
  train/validation/test splits (переважно temporal/grouped) та privacy policy.

## Результат

Dataset card, data dictionary, quality report і рішення «досить/недосить даних
для 152/153». Без такого рішення модель, інтерфейс або model price не пишуться.
