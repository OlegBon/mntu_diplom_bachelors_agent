# ADR-006: ізоляція synthetic demo dataset

**Статус:** погоджено для планування
**Дата:** 2026-09-24
**Пов'язані задачі:** 037, 060, 090, 095, 108, 121, 130, 131, 151, 153, 156–159

## Контекст

У `data/diamonds_dataset.csv` і local seed є 1 000 синтетичних records,
історично представлених як звичайні `DR-…` reports. Вони корисні для розробки
й technical SOM demo, але не є підтвердженим ринковим або навчальним джерелом.
Водночас Diamant ID потребує admin-only демонстраційного контуру: повні звіти,
media, паспортний вигляд, PDF та карта Кохонена без видимості експертам і без
змішування з operational даними.

## Рішення

### 1. Одна модель даних, два server-enforced scope

Demo не отримує дублікати `diamond_reports`, `stones`, `media_assets`,
`stone_valuations`, `report_events` або `public_passports`. У `DiamondReport`
додаються:

- `record_scope`: `operational` або `demo`, `NOT NULL`, default лише для
  operational create-flow;
- nullable `demo_dataset_id`, що посилається на окремий immutable manifest
  `demo_datasets` (`dataset_id`, label, version, generator/checksum,
  provenance, created_at, record_count, scope note, `analysis_eligibility`).

`analysis_eligibility` — не UI-прапорець і не висновок з `report_id`, а
server-enforced перелік дозволених сценаріїв набору: наприклад
`demo_operations` і `synthetic_som`. Аналітичний endpoint приймає лише
`dataset_id`, звіряє scope/provenance/eligibility та відбирає тільки reports
цього manifest. Arbitrary `DEMO-*`, historical `DR-*` або operational reports
не можуть бути непомітно додані до карти лише через ID або URL-параметр.

`Stone`, media, events, work sessions та valuations успадковують scope через
report. Це усуває роздвоєні migrations/CRUD/PDF і дає одну гарантію доступу.
`report_id` demo-записів має формат `DEMO-00001`; `DR-…` зарезервовано для
лише operational reports. `_next_report_id()` явно фільтрує `operational`, а
не покладається на лексичне сортування prefix-ів.

Постійного глобального перемикача «показувати demo» не додається: за
відсутності demo dataset режим просто недоступний. Якщо дані є, admin відкриває
їх лише через окремо позначений route/mode. Це не дає demo-даним випадково
з'явитися в звичайній роботі через localStorage, refresh або налаштування
іншого користувача.

### 2. Видимість, незмінність і API

- `gemologist` бачить, шукає, лічить і працює лише з `operational`. Прямий
  доступ до demo ID повертає однаковий `404`, не `403`.
- `admin` за замовчуванням теж отримує operational list. Demo відкривається
  лише явним admin-only dataset mode/route; змішаний список заборонений.
- Public `GET /public/passports/{public_id}` ніколи не повертає demo. Для demo
  не створюються `PublicPassport`, public code або QR.
- Demo records створює тільки trusted deterministic generator/seed; звичайні
  `POST /reports` payload і wizard не можуть задати scope/dataset.
- Demo records read-only через усі write paths: report update, transition,
  market attach, work-session, media upload/delete/publication, passport
  publish/reissue/revoke. Повертається контрольований `409` або `422` без
  часткових writes.
- Admin може відкрити private passport/PDF preview тим самим allow-listed
  renderer-ом, але без `public_passports` row. Preview/PDF мають помітне
  `DEMO · INTERNAL PREVIEW` watermark; вони не є документом для передачі.
- Генератор не приписує demo-звіт, подію чи вкладення реальному адміністратору
  або експерту. System-origin для 156 — `NULL` у nullable actor-посиланнях
  (`report_events.actor_id`, `stone_valuations.created_by_id`,
  `media_assets.uploaded_by_id`); UI показує «Synthetic demonstration dataset»,
  а не вигадану людину. Звичайне operational upload API, як і раніше, завжди
  встановлює `uploaded_by_id` поточного користувача.

### 3. Дані, медіа і ціна

Demo dataset детермінований, versioned і містить тільки synthetic або
ліцензовані assets. Не дозволяються реальні private report texts, files,
особи, OpenFacet/IDEX responses або невідомі image URLs.

Для demo використовується provenance `synthetic-demo-vN`, окремий
`valuation_kind` (наприклад `synthetic_demo_reference`) і source title
«Synthetic demonstration dataset». Це не legacy `DiamondReport.price`, не
market snapshot, не прогноз і не ринкова ціна.

Dashboard operational scope лишає заголовок **«Ціна (USD)»**, але прибирає
заголовкову `*` і legacy `d`. Поруч доступна коротка підказка «Довідкові
орієнтири, не ціна продажу». Кожен row показує незалежні type/source labels:
`SYS · OpenFacet`, `ADM · OpenFacet`, згодом `SYS · IDEX Online`; provider не
підміняє тип. `DEMO · synthetic-demo-vN` можливий лише у demo mode.

### 4. Поточні 1 000 seed records

`data/diamonds_dataset.csv` і `DR-00001…DR-01000` підтверджені як synthetic
project seed, який неодноразово регенерувався під час розвитку локальної схеми.
Перед реалізацією 156 складається read-only inventory і backup/rollback plan,
після чого migration класифікує цей діапазон як `demo` і прив'язує до manifest
без зміни фізичних
характеристик, lifecycle, legacy fields, valuations, events або ID. Rename
`DR-… → DEMO-…` не виконується для historical rows: він ламає FK, compatibility
та посилання. Новий generated demo dataset використовує `DEMO-…`.

Inventory перевіряє range, count, referential integrity і можливі локальні
ручні відхилення до backfill. Він не має очищувати або перекласифіковувати
`DR-01001+`: це окремі operational records, які лишаються недоторканими.

## Наслідки

- Потрібна Alembic revision, data migration тільки за окремим підтвердженням,
  isolated API/DOM/E2E tests та оновлення документації.
- Existing operational UI перестає показувати legacy demo money; дійсні
  market reference provenance не змінюються.
- Synthetic SOM demo (159) відокремлено від 153, де можливі лише якісні та
  ліцензовані real-world data.
- Demo lifecycle може бути синтетично позначений як `issued` лише для
  внутрішнього preview. Він не означає реальну видачу, не створює QR/public
  code і не потрапляє в operational лічильники, статистику чи черги.
- `analysis_eligibility=synthetic_som` дозволяє тільки technical demo 159.
  Він не є дозволом на verified ML, price prediction, investment claim або
  використання operational reports; для цього лишається окремий contract 151.
