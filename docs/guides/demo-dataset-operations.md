# Ізоляція synthetic demo dataset

## Призначення

`demo` — це окремий server-enforced scope для синтетичних демонстраційних
звітів. Він призначений для технічного показу workflow, майбутніх private
preview та SOM demo. Це не джерело експертних висновків, ринкових цін,
verified ML або публічних паспортів.

Операційний scope є стандартом для всіх звичайних endpoint-ів і майстра.
Дані scope не змішуються у списках, пошуку, пагінації, статистиці експертів,
review-cycle чи розрахунку наступного номера звіту.

## Схема та доступ

`diamond_oltp.diamond_reports` має `record_scope` (`operational` або `demo`)
та nullable `demo_dataset_id`. Для `operational` link має бути порожнім; для
`demo` він обов’язково посилається на immutable manifest `demo_datasets`.
Префікс ID не є контролем доступу: нові generator-звіти використовуватимуть
`DEMO-00001…`, але server завжди перевіряє scope і manifest.

Звичайні `/reports` маршрути показують лише `operational`. Експерт отримує
opaque `404` для demo ID. Адміністратор також не бачить demo у звичайному
списку чи detail; read-only доступ можливий лише через явні маршрути
`/demo/datasets/{dataset_id}` та `/demo/datasets/{dataset_id}/reports`.
Admin-only UI preview і private demo PDF реалізовані задачею 158. PDF містить
лише bundled synthetic photo/plotting assets і водяний знак `DEMO · INTERNAL
PREVIEW`; він не має public ID, URL, QR або anonymous media endpoint.

Усі regular write-маршрути відхиляють demo: update, transition, market
attachment, work-session, media та passport. Demo ніколи не має public
passport, public code, QR, анонімного media endpoint або публічного PDF.

## Manifest та аналітика

Manifest містить label/version, версію generator-а, checksum, provenance,
scope note, record count та JSON allow-list `analysis_eligibility`. Саме цей
allow-list, а не report ID або URL, надалі дозволить технічний сценарій на
кшталт `synthetic_som`. Він не дає права використати dataset для verified ML,
цінового прогнозу чи investment claim.

Synthetic generator не приписує report, event, session або media чинному
експерту чи адміністратору. System-origin — `NULL` у nullable actor-полях:
`report_events.actor_id`, `stone_valuations.created_by_id` і
`media_assets.uploaded_by_id`. Інтерфейс повинен показувати назву набору, а не
вигадану людину. Operational upload API не змінюється: він завжди записує
поточного автора.

## Генератор `synthetic-demo-v1`

Після застосування `0015_multi_provider_market_references` набір створює
окрема команда, а не `seed_db.py`. Вона не викликає OpenFacet, НБУ, IDEX,
публічні маршрути або scheduler.

Попередній перегляд є read-only: він показує ID набору, кількість записів і
SHA-256 майбутнього content manifest, але не відкриває сесію БД.

```powershell
.\.venv\Scripts\python.exe scripts\generate_synthetic_demo_dataset.py
```

Фактичний запис у локальну БД вимагає окремо погодженого явного параметра:

```powershell
.\.venv\Scripts\python.exe scripts\generate_synthetic_demo_dataset.py --apply
```

За замовчуванням generator створює рівно 1 000 `DEMO-00001…DEMO-01000`
записів за трирічний синтетичний період. Кожен має normalized `Stone`,
issued lifecycle, system/expert grades, безпечний короткий текст та два
незалежні `synthetic_demo_reference`: `Demo Market A` і `Demo Market B`.
Це вигадані джерела тільки в demo scope — вони не є OpenFacet, IDEX або НБУ
і не потрапляють до operational Market Data.

Повторний запуск із тим самим count/seed перевіряє manifest checksum і число
report rows та нічого не дублює. Інший count/seed або частковий набір
generator відхиляє без запису. Поточна реалізація навмисно не створює
вигадані account-и, work sessions або public passports: actor-поля
лишаються `NULL`. Вкладення preview — bundled presentation assets, а не
`media_assets`, тому їх неможливо опублікувати або отримати через URL.

## Historical `DR-00001…DR-01000`

Діапазон підтверджено як старий synthetic seed. Його не перейменовують у
`DEMO-…`, щоб не пошкодити foreign keys, сумісність і попередні посилання.
`DR-01001+` залишаються operational та не можуть бути очищені або
перекласифіковані цим процесом.

Перед будь-яким backfill необхідні всі кроки:

1. Створити backup локальних `diamond_oltp` і `diamond_market` перевіреним для
   вашого середовища інструментом MariaDB.
2. Запустити лише читання:

   ```powershell
   .\.venv\Scripts\python.exe scripts\inventory_demo_seed.py
   ```

3. Переконатися, що `ready_for_separate_backfill_approval` має значення `true`;
   немає missing/unexpected ID, report без Stone та orphan event у діапазоні.
4. Окремо погодити застосування Alembic `0014_demo_dataset_isolation`.
5. Окремо погодити й виконати classification backfill. Він може змінити лише
   `record_scope` та `demo_dataset_id` рівно для підтверджених historical rows;
   не змінює ID, Stone, lifecycle, valuation, event, media або public record.

Rollback класифікації повертає лише ці два поля до `operational`/`NULL` після
перевірки, що dataset не має нових generator-звітів. Schema downgrade не є
заміною для такого контрольованого rollback.

## Ціна у звичайному dashboard

Колонка `Ціна (USD)` показує лише versioned market reference, а не legacy
`DiamondReport.price`: `SYS · <provider>` означає автоматично сформований
орієнтир, `ADM · <provider>` — застосовність якого підтвердив адміністратор.
Це не продажна, транзакційна чи експертна ціна. Legacy demo marker `d` не
показується у operational UI; майбутній demo mode матиме окрему позначку
`DEMO · synthetic-demo-vN`.
