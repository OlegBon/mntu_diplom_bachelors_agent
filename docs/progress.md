# Журнал змін Diamant ID

Журнал фіксує зміни та перевірки Diamant ID.

Нові записи завжди додаються одразу під цим абзацом — у зворотному хронологічному порядку.
Кожен новий запис містить секції: **Задача**, **Змінені файли**, **Рішення / Результат**, **Перевірки**, **Нові змінні середовища**, **Обмеження**.

## 2026-09-23 — wizard-first-save-time

- **Задача:** додати до operational analytics окремий server-timed показник від першої взаємодії у майстрі до успішного створення першої чернетки.
- **Змінені файли:** `alembic/versions/0012_wizard_first_save_time.py`, `backend/{models,schemas,crud,main}.py`, `tests/{api/test_wizard_first_save_time,unit/test_migration_foundation}.py`, `frontend/src/js/modules/{api,report-wizard,wizard-work-session,analytics}.js`, `frontend/tests/e2e/{report-wizard,analytics}.spec.mjs`, `docs/{architecture,db-schema,api-mvp-audit,tech_diamant_id,work_plan,progress}.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/backlog/{README,113-wizard-first-save-time (видалено)}.md`.
- **Рішення / Результат:** `0012` додає nullable `first_save_started_at`/`time_to_first_save_seconds` до нового report та `wizard_work_sessions` як короткоживучий технічний lease. Лише видима дія gemologist стартує серверний lease; `POST /reports` атомарно claim-ить власний непрострочений UUID, записує elapsed duration і видаляє lease. Інша вкладка замінює попередній lease, а stale/offline/покинута спроба не блокує save й не створює operational metric. У деталях експерта metric показується окремими count/total/average/median, не змішаними з active-time saved draft.
- **Перевірки:** `python -m pytest tests/api/test_report_domain.py tests/unit/test_migration_foundation.py tests/api/test_wizard_first_save_time.py tests/api/test_expert_statistics.py -q` — 20 passed; `python -c "from backend.main import app; print(app.title)"` — успішно; `cmd /c "cd frontend && npm test"` — 20 passed; Playwright wizard + analytics — 2 passed; `alembic upgrade 0012_wizard_first_save_time --sql` — SQL згенеровано без зміни БД; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** це elapsed time, а не active-time; максимальний строк lease — 4 години. До застосування `0012` локальна MariaDB не має потрібних таблиці й полів. Немає historical backfill або scheduler-а для фонової очистки покинутих lease: прострочені записи прибираються при наступному start майстра.

## 2026-09-23 — analytics-period-feedback

- **Задача:** зробити застосований період operational analytics очевидним без потреби візуально порівнювати таблиці.
- **Змінені файли:** `frontend/src/{pug/pages/ml-analysis.pug,js/modules/analytics.js,scss/_ui-primitives.scss}`, `frontend/tests/{page-dom,e2e/analytics}.mjs`, `docs/progress.md`.
- **Рішення / Результат:** під period-filter додано доступний live-статус «Поточний зріз». Він одразу показує «за весь доступний час», а після успішного завантаження показує фактичний діапазон «з … до …», лише нижню або лише верхню межу. «За весь час» очищує поля й повертає цей стан.
- **Перевірки:** `cmd /c "cd frontend && npm test"` — 20 passed; `npx playwright test tests/e2e/analytics.spec.mjs` — 1 passed; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** статус підтверджує застосований діапазон лише після успішної відповіді API; при помилці залишається попередній успішний зріз, а причина показується стандартним повідомленням помилки.

## 2026-09-22 — expert-active-time-and-analytics-periods (завершено)

- **Задача:** достовірно обліковувати active-time автора draft без обліку просто відкритої вкладки та додати period filters до operational analytics.
- **Змінені файли:** `alembic/versions/0011_expert_work_sessions.py`, `backend/{models,schemas,crud,main}.py`, `tests/{api/test_expert_statistics,unit/test_migration_foundation}.py`, `frontend/src/{pug/pages/ml-analysis.pug,scss/_ui-primitives.scss,js/modules/{api,analytics,report-detail,report-work-session}.js}`, `frontend/tests/{auth-and-api,page-dom,e2e/{analytics,report-detail}}.mjs`, `docs/{architecture,db-schema,api-mvp-audit,tech_diamant_id,work_plan,progress}.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/backlog/{README,112-expert-active-time-and-analytics-periods (видалено)}.md`.
- **Рішення / Результат:** `0011` додає порожні `report_work_sessions`, append-only `report_work_session_events` і single-tab `report_work_session_leases`. Лише owner-`gemologist` saved `draft` стартує сесію після реальної дії в editable detail; server-time обмежує кожен інтервал 60 секундами, lease спливає за 75 секунд, друга вкладка закриває попередню, hidden/offline/page-close не додають час, а `draft → review` завершує активну сесію server-side. Admin analytics показує total/average/median та три короткі/довгі завершені сесії; `date_from`/`date_to` означають creation date для status counts, finish date для active-time та decision date для review-cycle.
- **Перевірки:** `python -m pytest tests/unit -q` — 14 passed; `python -m pytest tests/api/test_expert_statistics.py -q` — 4 passed; `python -m pytest tests/api/test_report_domain.py tests/api/test_report_media.py -q` — 8 passed; `python -m pytest tests/api/test_public_passport_pdf.py -q` — 2 passed; `cmd /c "cd frontend && npm test"` — 20 passed; targeted Playwright analytics/detail — 2 passed; `npm run build` — успішно.
- **Нові змінні середовища:** немає.
- **Обмеження:** до першого save wizard не має report ID, тому active-time ще не починається; історичні reports і legacy `evaluation_time_sec` не backfill-яться. `0011_expert_work_sessions` створена, але не застосована до локальної MariaDB без окремого підтвердження. Метрика є operational record, не рейтингом чи оцінкою продуктивності.

## 2026-09-18 — backlog-market-provider-operations (завершено)

- **Задача:** прибрати завершену 121 з активного backlog, винести її нереалізований операційний залишок у самостійну задачу та виправити застаріле посилання 115.
- **Змінені файли:** `docs/backlog/{README,121-market-data-provider-expansion-and-fx (видалено),122-market-provider-operations,115-profile-admin-ui-polish}.md`, `docs/{work_plan,progress}.md`.
- **Рішення / Результат:** 121 лишається завершеною roadmap-задачею без active backlog-файлу. Freshness policy, scheduler, observability, нові provider-и та рішення про public/PDF-відображення чітко відокремлено у новій активній 122. 115 тепер посилається на чинну 112 замість видаленої 108.
- **Перевірки:** звірено стан `docs/backlog/`, активні позначки `work_plan.md` і журнал `progress.md`; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** 122 є планом, а не реалізацією scheduler-а, freshness policy чи нового зовнішнього provider-а.

## 2026-09-18 — market-data-documentation-reconciliation (завершено)

- **Задача:** актуалізувати документацію після завершення OpenFacet/NBU/policy контуру та додавання audit-подій ринкових орієнтирів.
- **Змінені файли:** `docs/{architecture,db-schema,api-mvp-audit,work_plan}.md`, `docs/decisions/002-financial-calculation-contract.md`, `docs/progress.md`.
- **Рішення / Результат:** документація синхронізована з локально застосованою `0010_market_reference_policy`: описані policy, НБУ, immutable provenance і private audit-події для фактично нових valuations. Явно зафіксовано відсутність backfill для historical valuations та подій, аби історія не містила штучно реконструйованих фактів.
- **Перевірки:** звірено з `backend/crud.py`, API-маршрутами та `scripts/audit-api.mjs`; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** API audit навмисно залишається read-only і не тестує external fetch/approve/write сценарії; їх покривають ізольовані pytest та Playwright-набори.

## 2026-09-18 — market-reference-report-history (завершено)

- **Задача:** доповнити private «Історію змін» звіту подіями про створення ринкових довідкових орієнтирів.
- **Змінені файли:** `backend/crud.py`, `frontend/src/js/modules/report-detail.js`, `tests/api/test_market_data.py`, `frontend/tests/e2e/report-detail.spec.mjs`, `docs/guides/{current-domain-and-report-workflow,market-data-providers}.md`, `docs/progress.md`.
- **Рішення / Результат:** створення нового immutable `system_market_reference` додає подію «Системний довідковий орієнтир додано», а ручне admin-підтвердження `market_reference` — «Довідковий орієнтир підтверджено адміністратором». Кожна подія зберігає private контекст: суму, провайдера і snapshot. Запис події входить до тієї самої транзакції, що й valuation; ідемпотентне повторне збереження без нового valuation не створює дубль події.
- **Перевірки:** `python -m compileall -q backend` — успішно; `pytest tests/api/test_market_data.py -q` — 5 passed; `frontend npm test` — 20 passed; Playwright `report-detail.spec.mjs` — 1 passed; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** історія показує факт приватного орієнтиру, а не експертну, продажну чи транзакційну ціну; дані цін, як і раніше, не передаються в public passport або PDF.

## 2026-09-18 — market-reference-disclosure-indicator (завершено)

- **Задача:** зробити стан розкриття історичних ринкових орієнтирів помітним у private detail.
- **Змінені файли:** `frontend/src/scss/_ui-primitives.scss`, `docs/progress.md`.
- **Рішення / Результат:** у правому верхньому куті summary додано SVG-стрілку в стилі select: вниз для згорнутого `details`, вгору для відкритого. Нативний marker приховано, але semantic `summary` і keyboard behavior збережені; додано видимий focus state.
- **Перевірки:** `frontend npm test` — 20 passed; Playwright `report-detail.spec.mjs` — 1 passed.
- **Нові змінні середовища:** немає.
- **Обмеження:** індикатор відображає стан нативного `details`; не вводить окремого JavaScript-стану чи змін у даних valuations.

## 2026-09-18 — collapse-historical-market-references (завершено)

- **Задача:** зробити private detail звіту читабельним після кількох автоматичних системних ринкових орієнтирів.
- **Змінені файли:** `frontend/src/{js/modules/report-detail.js,scss/_ui-primitives.scss}`, `frontend/tests/e2e/report-detail.spec.mjs`, `docs/progress.md`.
- **Рішення / Результат:** API та immutable історія valuations не змінюються. Detail показує найновіший ринковий орієнтир відкритим, а попередні зберігає згорнутими у доступних нативних `details/summary`; у summary залишаються сума та тип, а розкриття показує повний provenance, UAH і курс. Користувач може переглянути будь-який історичний запис.
- **Перевірки:** `frontend npm test` — 20 passed; Playwright `report-detail.spec.mjs` — 1 passed, включно зі станом двох valuations і ручним розкриттям попередньої.
- **Нові змінні середовища:** немає.
- **Обмеження:** «найновіший» означає перший запис у чинному private API, тобто `created_at DESC, valuation_id DESC`; логіка пріоритету ручного reference у dashboard не змінюється.

## 2026-09-17 — prevent-implicit-wizard-draft-submit (завершено)

- **Задача:** прибрати випадкове створення чернетки в майстрі через клавішу Enter.
- **Змінені файли:** `frontend/src/js/modules/report-wizard.js`, `frontend/tests/e2e/report-wizard.spec.mjs`, `docs/progress.md`.
- **Рішення / Результат:** Enter у звичайних текстових, числових, date та споріднених `input` не виконує implicit HTML submit. `textarea`, file input, select і клавіатурна активація явно сфокусованої кнопки не змінені. Чернетка створюється тільки явною дією «Зберегти чернетку», а кнопка як і раніше блокується на час запиту.
- **Перевірки:** `frontend npm test` — 20 passed; Playwright `report-wizard.spec.mjs` — 1 passed, зокрема Enter не створює чернетку, а click створює один запис.
- **Нові змінні середовища:** немає.
- **Обмеження:** це frontend-захист від випадкового submit; server-side валідація та захист від дублювання залишаються авторитетними.

## 2026-09-17 — clarify-idc-methodology-in-wizard (завершено)

- **Задача:** прибрати внутрішній code `idc-demo-v1` з user-facing preview майстра та чітко назвати його методичну основу.
- **Змінені файли:** `backend/crud.py`, `frontend/src/{pug/pages/create-report.pug,js/modules/report-wizard.js}`, `docs/{progress,guides/current-domain-and-report-workflow,guides/idc-demo-v1-ruleset}.md`.
- **Рішення / Результат:** майстер показує `IDC Rules for Grading Polished Diamonds, 6th edition (2013)` і межу «спрощений системний розрахунок Diamant ID; не є сертифікацією IDC». `idc-demo-v1` збережено лише як immutable внутрішній ідентифікатор API/БД для відтворюваності історичних grades; у коді та guide прямо зафіксовано, що це не назва й не версія документа. Назву джерела звірено за титульною сторінкою локального PDF; `July` не входить до неї.
- **Перевірки:** `frontend npm test` — 20 passed; `python -m pytest tests/api/test_report_domain.py tests/unit/test_migration_foundation.py -q` — 11 passed.
- **Нові змінні середовища:** немає.
- **Обмеження:** документ 2013 року не названо «останньою редакцією IDC», бо для такого твердження потрібна окрема перевірка актуальних публікацій IDC.

## 2026-09-17 — wizard-policy-market-reference-preview (завершено)

- **Задача:** замінити legacy demo-прогноз `USD … d` у майстрі створення звіту на системний довідковий USD-орієнтир із поточної admin policy.
- **Змінені файли:** `backend/{crud,schemas}.py`, `tests/api/{test_report_domain,test_market_data}.py`, `frontend/src/{pug/pages/create-report.pug,js/modules/report-wizard.js}`, `frontend/tests/e2e/report-wizard.spec.mjs`, `docs/{architecture,db-schema,work_plan,progress}.md`, `docs/guides/{current-domain-and-report-workflow,market-data-providers}.md`.
- **Рішення / Результат:** `POST /reports/preview` приймає shape/origin і читає обраного policy-провайдера та останній застосовний approved snapshot. Для OpenFacet повертає total USD, код `openfacet` і snapshot ID; майстер показує `USD … of`, назву джерела й попередження, що значення ще не зафіксовано. За відсутності покриття показує зрозуміле повідомлення без блокування заповнення. Preview не створює `StoneValuation` і не отримує НБУ; під час збереження draft сервер повторно застосовує policy, створює immutable reference та, якщо policy увімкнула FX, фіксує курс і UAH.
- **Перевірки:** `python -m compileall -q backend` — успішно; `python -m pytest tests/api/test_report_domain.py tests/api/test_market_data.py tests/unit/test_migration_foundation.py -q` — 16 passed; `frontend npm test` — 20 passed; Playwright `report-wizard.spec.mjs` — 1 passed.
- **Нові змінні середовища:** немає.
- **Обмеження:** preview підтримує лише провайдери, для яких існує server adapter; зараз це OpenFacet. Зміна policy або approval новішого snapshot-а між preview і save може змінити остаточно зафіксований орієнтир; це свідомо, бо майстер не резервує snapshot.

## 2026-09-17 — market-policy-control-and-fx-format-polish (завершено)

- **Задача:** виправити розтягнутий radio-control policy провайдера на «Ринкові дані» та прибрати штучні нулі з відображення зафіксованого курсу НБУ.
- **Змінені файли:** `frontend/src/{pug/pages/market-data.pug,scss/_ui-primitives.scss,js/modules/{market-data,dashboard,report-detail}.js}`, `docs/progress.md`.
- **Рішення / Результат:** policy radio отримав окремий компактний flex/card-стиль без успадкування checkbox-layout; він однаково працює в desktop і mobile flow. БД зберігає FX rate із точністю `DECIMAL(18,8)`, але private detail і dashboard popover показують локалізоване число максимум із вісьмома значущими десятковими знаками без trailing zeros: `44.6648 UAH/USD` замість `44.66480000`.
- **Перевірки:** `frontend npm run build` — успішно; Node/jsdom tests — 20 passed; Playwright market-data — 1 passed; `git diff --check` — без помилок. Browser-вікно цієї сесії недоступне, тому візуальний screenshot QA не виконано.
- **Нові змінні середовища:** немає.
- **Обмеження:** currency formatting застосовано до dashboard/private detail; сутність rate і API зберігають повну Decimal-точність. Потрібна коротка ручна перевірка відрендереного desktop і mobile control після оновлення BrowserSync.

## 2026-09-17 — configurable-market-reference-policy (завершено)

- **Задача:** завершити 121 керованою admin policy для провайдерів, прибрати `*` з самого значення ціни та відокремити legacy `market_price_reference` від нового ринкового контуру.
- **Змінені файли:** `alembic/versions/0010_market_reference_policy.py`, `backend/{crud,main,models,schemas}.py`, `tests/{api/test_market_data,unit/test_migration_foundation}.py`, `frontend/src/{pug/pages/{dashboard,market-data}.pug,js/modules/{api,dashboard,market-data}.js}`, `frontend/tests/{auth-and-api,profile-admin-pages,e2e/market-data}.mjs`, `scripts/audit-api.mjs`, `docs/{architecture,api-mvp-audit,db-schema,work_plan,progress}.md`, `docs/{guides/current-domain-and-report-workflow,market-data-providers}.md`, `docs/backlog/121-market-data-provider-expansion-and-fx.md`.
- **Рішення / Результат:** `0010` додає singleton `market_reference_policies`: обраний market provider, прапорець FX та обраний FX provider для лише майбутніх системних орієнтирів. Початкове значення зберігає `openfacet` + `nbu`; historical snapshot-и, valuations і legacy demo-індекс не змінюються. Admin API/UI дозволяє обрати market provider radio-кнопкою й вимкнути UAH-конвертацію. Автоматичний та ручний reference читають policy; при вимкненому FX USD зберігається без UAH. У dashboard заголовок — `Ціна (USD)*`, `*` пояснює системний характер колонки, а значення OpenFacet має `of` незалежно від автоматичного чи ручного походження; detail/popover зберігають різницю типів.
- **Перевірки:** `python -m pytest tests/api/test_market_data.py tests/unit/test_nbu_fx.py tests/unit/test_migration_foundation.py -q` — 11 passed; `python -m compileall -q backend` і import FastAPI — успішно; `alembic upgrade head --sql` — успішно; фактичний `alembic upgrade head` — `0009 → 0010`; `alembic current` — `0010_market_reference_policy (head)`; read-only MariaDB check підтвердив policy `1 / openfacet / FX=1 / nbu`; `frontend npm run build`, Node/jsdom tests — 20 passed; Playwright market-data — 1 passed; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** Singleton гарантується server-side фіксованим `policy_id=1`: MariaDB 10.4 не дозволяє `CHECK` над `AUTO_INCREMENT`, тому SQL `CHECK` не використовується. Підтриманими server adapter-ами лишаються тільки OpenFacet і НБУ; radio-контроль не робить невідомий provider робочим. Немає scheduler, freshness SLA, retries/backoff чи historical backfill.

## 2026-09-17 — automatic-system-market-reference (завершено)

- **Задача:** завершити 121 автоматичним системним довідковим орієнтиром для підтримуваних нових та оновлених draft-звітів, не змішуючи його з ручним admin-підтвердженням.
- **Змінені файли:** `backend/{crud,main,schemas}.py`, `tests/api/test_market_data.py`, `frontend/src/{js/modules/{dashboard,report-detail}.js,pug/pages/dashboard.pug}`, `frontend/tests/page-dom.test.mjs`, `docs/{architecture,db-schema,work_plan,progress}.md`, `docs/{decisions/002-financial-calculation-contract.md,guides/current-domain-and-report-workflow.md,backlog/121-market-data-provider-expansion-and-fx.md}`.
- **Рішення / Результат:** після створення або зміни підтримуваного draft сервер best-effort бере останній approved OpenFacet snapshot, розраховує immutable `system_market_reference` і фіксує USD/UAH разом з новим NBU snapshot-ом. Відсутні snapshot/coverage або НБУ не блокують save; ідентичні market-входи не створюють дублі. Ручний `market_reference` з поясненням застосовності лишається окремим і пріоритетним. У «Всі звіти» заголовок збережено як «Ціна (USD)»: `*` означає «Системний довідковий орієнтир (USD)», `of` — ручне admin-підтвердження, `d` — legacy demo. Private detail і popover пояснюють provenance; public passport/PDF цін не отримують.
- **Перевірки:** `python -m pytest tests/api/test_market_data.py tests/unit/test_nbu_fx.py -q` — 5 passed; `python -m compileall -q backend` — успішно; `frontend npm test` — 20 passed; `frontend npm run test:e2e` — 14 passed; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** немає scheduler/freshness SLA, retry/backoff або historical backfill. Автоматичний орієнтир застосовується лише до майбутнього create/draft update, не є експертною, продажною чи транзакційною ціною, а OpenFacet coverage обмежена natural stone та наявними shape/color/clarity/carat anchors.

## 2026-09-17 — report-workflow-market-reference-guide (завершено)

- **Задача:** доповнити наскрізний guide фактичною механікою market reference, OpenFacet та frozen NBU USD/UAH.
- **Змінені файли:** `docs/guides/current-domain-and-report-workflow.md`, `docs/progress.md`.
- **Рішення / Результат:** guide тепер розмежовує `d`, `of` і відсутнє значення, пояснює private/public межу та містить практичний приклад `DR-01004`: candidate, approve, applicability, OpenFacet interpolation, автоматичний NBU fetch, immutable USD/UAH provenance і відображення у detail/dashboard.
- **Перевірки:** перевірено посилання, терміни та відповідність чинному контракту `0009_nbu_fx_snapshots`; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** guide не вводить scheduler, historical reprice, інший provider або price у public passport/PDF.

## 2026-09-17 — market-reference-presentation-polish (завершено)

- **Задача:** уніфікувати дату НБУ у dashboard popover і зробити private presentation довідкового ринкового орієнтира читабельним.
- **Змінені файли:** `frontend/src/js/modules/{dashboard,report-detail}.js`, `frontend/src/scss/_ui-primitives.scss`, `docs/progress.md`.
- **Рішення / Результат:** popover показує official rate date у форматі `uk-UA`, як і private detail. Один перевантажений рядок detail замінено на flat-card із основною USD-сумою, визначеними полями provenance, frozen UAH/NBU і відокремленим поясненням застосовності; mobile складає пари у одну колонку.
- **Перевірки:** `npm run build` — успішно; frontend Node/jsdom tests — 20 passed; Playwright E2E — 14 passed; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** це лише presentation private market reference; розрахунок, FX snapshot, passport і PDF не змінені.

## 2026-09-17 — nbu-fx-for-market-references (завершено)

- **Задача:** завершити 121: додати НБУ USD/UAH до контрольованого OpenFacet market-reference без переоцінки історії або відкриття ціни у passport/PDF.
- **Змінені файли:** `alembic/versions/0009_nbu_fx_snapshots.py`, `backend/{fx,crud,main,models,schemas}.py`, `tests/{unit/test_nbu_fx,api/test_market_data}.py`, `frontend/src/{js/modules/{api,dashboard,market-data,report-detail}.js,pug/pages/{dashboard,market-data}.pug}`, `frontend/tests/{auth-and-api,page-dom}.test.mjs`, `docs/{architecture,db-schema,local-start,work_plan,progress}.md`, `docs/{decisions/002-financial-calculation-contract.md,guides/current-domain-and-report-workflow.md,backlog/121-market-data-provider-expansion-and-fx.md}`.
- **Рішення / Результат:** `0009` реєструє `nbu`, створює immutable `fx_data_snapshots` та nullable frozen FX/UAH поля для лише нових `stone_valuations`. Attach approved OpenFacet snapshot-а повторно отримує official USD/UAH НБУ, у тій самій транзакції зберігає rate, official rate date, FX snapshot і UAH total. Помилка НБУ повертає 502 та не дозволяє непомітно використати старий курс. Admin може вручну створити контрольний NBU snapshot. Dashboard показує `USD … d` для legacy demo або `USD … of` для OpenFacet; popover і private detail пояснюють USD, UAH та provenance. Passport і PDF не містять цін.
- **Перевірки:** backend pytest — 42 passed (запуск групами через обмеження локального runner-а); `npm test` — 20 passed; `npm run test:e2e` — 14 passed; `alembic upgrade head --sql` — успішно; фактичний `alembic upgrade head` — `0008 → 0009`; `alembic current` — `0009_nbu_fx_snapshots (head)`; read-only smoke з офіційним НБУ endpoint успішний; `git diff --check` — без помилок.
- **Нові змінні середовища:** немає.
- **Обмеження:** немає scheduler, retries/backoff, historical backfill, нового комерційного провайдера чи public/PDF price policy. OpenFacet лишається довідковим benchmark, не appraisal/offer/transaction/sale price.

## 2026-09-17 — authoritative-market-data-providers (завершено)

- **Задача:** завершити 110: створити безпечний розширюваний контур ринкових даних з першим OpenFacet adapter-ом без підміни legacy/demo ціни.
- **Змінені файли:** `alembic/versions/{0007_grading_rulesets,0008_market_data_providers}.py`, `backend/{crud,main,market_providers,models,schemas}.py`, `frontend/src/{pug/{pages/{market-data,report-detail}.pug},js/{main,modules/{api,market-data,report-detail}.js},scss/_ui-primitives.scss}`, `frontend/tests/{auth-and-api,profile-admin-pages,e2e/market-data}.mjs`, `tests/{api/test_market_data.py,unit/{test_market_providers,test_migration_foundation}.py}`, `scripts/audit-api.mjs`, `docs/{architecture,db-schema,api-mvp-audit,work_plan,progress}.md`, `docs/decisions/002-financial-calculation-contract.md`, `docs/backlog/{121-market-data-provider-expansion-and-fx.md,110-authoritative-market-data-and-fx.md (видалено)}`.
- **Рішення / Результат:** `diamond_market` має provider catalog і immutable `candidate → approved/rejected` snapshots з normalized USD/ct quotes, provenance і SHA-256. Admin вручну отримує OpenFacet candidate, приймає рішення через штатну модалку з необов’язковим коментарем та може явно прикріпити approved `market_reference` до natural-звіту з поясненням застосовності. Відмова через непокриття OpenFacet (зокрема `lab_grown`) показується українською прямо біля форми, а не лише як HTTP 422 у console. Private detail показує збережений орієнтир окремим блоком із сумою, провайдером, snapshot-ом, датою та підтвердженням застосовності. Legacy `DiamondReport.price`, dashboard/wizard `USD … d`, public passport і PDF не змінюються. `/market-data/*` закритий admin RBAC; safe audit перевіряє його 401-межі. `0008_market_data_providers` застосовано до локальної MariaDB.
- **Перевірки:** цільові pytest — 7 passed; `npm test` — 20 passed; Playwright market-data — 1 passed, повний `npm run test:e2e` до UI-уточнення — 14 passed; static `alembic upgrade head --sql` — успішно; фактичний `alembic upgrade head` — `0007 → 0008`; read-only SQL підтвердив OpenFacet provider, `0` snapshot-ів і `0` наявних valuations з snapshot provenance; `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** OpenFacet — model-based retail benchmark, не appraisal/offer/transaction/sale price; чинний report не зберігає laboratory certificate, тому applicability підтверджує admin. Немає NBU FX/UAH, scheduler, freshness policy, автоматичного прикріплення чи показу суми клієнту/PDF. Розширення винесено в 121; перед зовнішнім або комерційним відображенням потрібна окрема перевірка умов провайдера.

## 2026-09-17 — e2e-regression-and-api-audit-refresh (завершено)

- **Задача:** актуалізувати застарілі E2E-очікування після admin modal, public passport і detail validation, а також синхронізувати historical API audit із чинним safe smoke-контрактом.
- **Змінені файли:** `frontend/tests/{auth-and-api.test.mjs,e2e/{profile-admin,public-passport-controls,public-passport-delivery,report-detail-confirmation-grades}.spec.mjs}`, `scripts/audit-api.mjs`, `docs/{api-mvp-audit,work_plan,progress}.md`.
- **Рішення / Результат:** E2E перевіряє модальний flow «Змінити» → «Деактивувати», повний admin test-session для private passport і всі server-required reference mappings у detail flow. API-клієнт має test для обох protected analytics endpoints. Safe audit додатково перевіряє без токена `/reference-values`, `/statistics/expert-performance` і `/statistics/admin-review-performance`; актуальна кількість перевірок — 13. `api-mvp-audit.md` відокремлює історичний стан 14.09 від чинного реалізованого контракту.
- **Перевірки:** `pytest` — 36 passed; `npm test` — 18 passed; `npm run test:e2e` — 13 passed; `npm run audit:api` — 13/13 проти локального backend; `node --check scripts/audit-api.mjs`; `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** safe audit навмисно не виконує login, POST, PUT, DELETE, seed або міграції. Він не замінює auth/RBAC integration tests чи ручне приймання UI.

## 2026-09-17 — expert-operational-analytics (завершено)

- **Задача:** завершити 108: виправити admin-only контракт operational analytics, показати перевірені status/review metrics у UI та зафіксувати межі майбутнього active-time і stone analytics.
- **Змінені файли:** `backend/{crud,main,schemas}.py`, `tests/api/test_expert_statistics.py`, `frontend/src/{pug/pages/ml-analysis.pug,js/{main,modules/{api,analytics}.js},scss/{main,_ui-primitives}.scss}`, `frontend/tests/{page-dom.test.mjs,e2e/analytics.spec.mjs}`, `docs/{architecture,work_plan,progress}.md`, `docs/backlog/{README,112-expert-active-time-and-analytics-periods,120-legacy-calculation-and-ml-boundary}.md`; `docs/backlog/108-expert-statistics-and-analytics-contract.md` видалено.
- **Рішення / Результат:** `/statistics/expert-performance` доступний лише admin і повертає all-time статусні лічильники gemologist-ів без штучного рейтингу чи середньої ваги. `/statistics/admin-review-performance` показує тривалість review-cycle від передачі до рішення admin, а не активний час людини, включно з середньою, медіаною та трьома найкоротшими/найдовшими завершеними циклами. «Аналітика» має вкладки «Експерти», «Адміністратори», «Камені»; остання не імітує ML-графіки. Картка експерта відкриває деталі наявних даних. Глобальний `scrollbar-gutter` прибирає стрибок ширини при появі вертикального scrollbar.
- **Перевірки:** `pytest tests/api/test_expert_statistics.py -q` — 2 passed; `npm test` — 17 passed; Playwright `analytics.spec.mjs` — 1 passed; FastAPI import smoke; `git diff --check`. Ручно підтверджено UI до merge.
- **Нові змінні середовища:** немає.
- **Обмеження:** active-time, дата початку роботи експерта, періодні фільтри й списки найшвидших/найдовших фактичних сесій не відновлюються з приблизних дат; це окрема 112. Карти Кохонена та інша аналітика каменів потребують перевіреного джерела/ML-контракту в 120.

## 2026-09-17 — versioned-idc-rulesets-and-report-actions (завершено)

- **Задача:** завершити 105: зафіксувати межі `idc-demo-v1`, версіонувати методику без зміни історичних звітів, прибрати ручний Final Cut та узгодити workflow і дії списку звітів.
- **Змінені файли:** `alembic/versions/0007_grading_rulesets.py`, `backend/{calculator,crud,models,schemas}.py`, `frontend/src/{pug/pages/report-detail.pug,js/modules/{dashboard,report-detail}.js,scss/_ui-primitives.scss}`, `frontend/tests/e2e/{dashboard,report-detail,report-detail-confirmation-grades}.spec.mjs`, `tests/{api/test_report_domain.py,unit/test_migrations.py}`, `docs/{architecture,db-schema,work_plan,progress}.md`, `docs/guides/{README,current-domain-and-report-workflow,idc-demo-v1-ruleset}.md`; `docs/backlog/105-versioned-reference-catalogs.md` видалено.
- **Рішення / Результат:** `grading_rulesets` містить immutable metadata активного `idc-demo-v1` та legacy marker; нові звіти отримують активну версію, historical не перераховуються. Polish, Symmetry і експертний Proportions вводить експерт, а підсумковий Cut сервер обчислює детерміновано. У dashboard редагування доступне лише для `draft`; «Друк» відкриває private detail і системний діалог друку. Guide спочатку подає коди статусів і UI-підписи, а потім повний workflow.
- **Перевірки:** міграцію `0007_grading_rulesets` застосовано до локальної MariaDB і перевірено read-only SQL; цільові backend-тести — 34 passed; `npm test` — 16 passed; Playwright dashboard і report detail — 2 passed; `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** `idc-demo-v1` — спрощена методика, не повна сертифікація IDC 2013. Admin UI не редагує формули чи межі: нова IDC-методика потребує окремого аналізу, ruleset, міграції та тестових векторів. «Друк» — внутрішній private report; документ для покупця залишається public passport PDF.

## 2026-09-17 — backlog-hygiene-after-task-100 (завершено)

- **Задача:** прибрати виконану 100 з активного backlog і окремо зафіксувати наступний UI-polish.
- **Змінені файли:** `docs/{backlog/{README,100-profile-and-admin-ui (видалено),110-authoritative-market-data-and-fx,115-profile-admin-ui-polish}.md,work_plan,progress}.md`.
- **Рішення / Результат:** 100 позначена завершеною у roadmap без посилання на активний backlog; створено 115 для майбутніх узгоджених дизайн- та responsive-покращень без розширення scope 100.
- **Перевірки:** внутрішні Markdown-посилання й `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** конкретні дизайн-зауваження будуть додані в 115 після окремого обговорення; runtime-код не змінювався.

## 2026-09-16 — password-visibility-and-stale-data-refresh (завершено)

- **Задача:** додати однаковий доступний показ пароля та не залишати застарілі read-only дані у відкритих вкладках.
- **Змінені файли:** `frontend/src/js/{main.js,modules/{password-visibility,page-refresh,dashboard,report-detail,admin-users,reference-catalog,public-passport}.js}`, `frontend/src/scss/_ui-primitives.scss`, `docs/{architecture,work_plan,progress}.md`.
- **Рішення / Результат:** усі password inputs отримують кнопку-«око» з доступними назвами «Показати пароль» / «Сховати пароль»; пароль не зберігається та не виводиться у повідомлення. Dashboard, private detail поза edit mode, admin directory, довідники й public passport повторно читають сервер при поверненні фокусу та раз на 30 секунд у видимій вкладці. Wizard, profile і detail edit не оновлюються автоматично, щоб не втратити незбережений ввід. Уточнено `docs/architecture.md` і актуалізовано застарілі пункти `docs/work_plan.md` про profile/admin UI.
- **Перевірки:** `npm test` — 16 passed; `npm run test:e2e` — 11 passed. Один наявний admin E2E ще очікує застарілу inline-кнопку «Деактивувати» замість чинного flow «Змінити» → модалка; код функціоналу не змінювався заради цього старого очікування. `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** це client-side polling, а не WebSocket/SSE: зміна іншого користувача з’являється після повернення у вкладку або максимум через 30 секунд. Автооновлення свідомо не торкається форм із можливим незбереженим вводом.

## 2026-09-16 — admin-user-tablet-layout (завершено)

- **Задача:** зробити directory облікових записів читабельним на ширинах 768–1024 px.
- **Результат:** у tablet-діапазоні таблиця переходить у сітку з двох карток у ряд із підписами полів, тому колонки не стискаються й не виходять за межі блока; desktop і mobile presentation не змінені.
- **Перевірки:** `npm test` — 16 passed.

## 2026-09-16 — admin-user-modal-and-password-reset (завершено)

- **Задача:** спростити admin directory та додати контрольований reset пароля.
- **Результат:** список облікових записів read-only; «Змінити» відкриває модалку для ПІБ, username, ролі, status і нового тимчасового пароля. Пароль зберігається лише через bcrypt hash. Admin може змінити власний username також у Profile, після чого стара JWT-сесія завершується. Header показує фактичний username, а не статичний `Admin`.
- **Перевірки:** `pytest tests/api/test_profile_and_admin.py` — 6 passed; `npm test` — 16 passed.

## 2026-09-16 — admin-user-directory-pagination (завершено)

- **Задача:** розширити admin directory пошуком, server-side пагінацією та завершити mobile presentation.
- **Результат:** `GET /users/` повертає scoped `items/total/page/page_size/total_pages`; admin UI має пошук за username/іменем і reusable pagination component. Власна зміна username завершує стару JWT-сесію та веде до повторного входу. Mobile-картки мають окремі межі, відступи й повноширинні дії.
- **Перевірки:** `pytest tests/api/test_profile_and_admin.py` — 6 passed; `npm test` — 16 passed; Playwright profile/admin — 2 passed; `git diff --check` — успішно.

## 2026-09-16 — admin-users-catalog-layout (завершено)

- **Задача:** уточнення admin UI після ручної перевірки.
- **Результат:** admin може змінювати унікальний username через явну дію збереження; після зміни власного username потрібен повторний login. Таблиця облікових записів має контрольовані колонки й scroll на вузьких екранах, select мають видимий індикатор. Довідники згруповано за читабельними бізнес-категоріями.
- **Перевірки:** `pytest tests/api/test_profile_and_admin.py` — 5 passed; `npm test` — 16 passed; `git diff --check` — успішно.

## 2026-09-16 — profile-and-admin-ui (завершено)

- **Задача:** профіль, безпечне admin-керування експертами та read-only server-side довідники.
- **Результат:** користувач змінює лише ПІБ і пароль з перевіркою поточного пароля; `username` і роль read-only. Admin створює користувачів, змінює ролі, деактивує/активує акаунти без hard delete. Inactive акаунт не проходить login і не використовує старий JWT; self-deactivate та втрата останнього active admin заблоковані. Версіоновані довідники й статистика винесені у 105/108.
- **Міграція:** додано `0006_expert_activation`; не застосовувалася до локальної MariaDB без окремого дозволу.
- **Перевірки:** цільові API tests 8 passed; `npm test` 16 passed; Playwright profile/admin 2 passed; FastAPI import smoke і `git diff --check` успішні. Browser integration була недоступна, тому rendered UI перевірено штатним Playwright fallback.

## 2026-09-16 — local-mariadb-console-runbook (завершено)

- **Задача:** додати безпечну альтернативу XAMPP Control Panel для запуску й діагностики локальної MariaDB.
- **Змінені файли:** `docs/{local-start,progress}.md`.
- **Результат:** `local-start.md` містить перевірені console-команди для `mysqld`, `tasklist`, TCP connection check і read-only контроль `diamond_oltp`/`alembic_version`; описано штатне завершення через `Ctrl+C` або `mysqladmin shutdown` та межу між діагностикою і recovery.
- **Перевірки:** синтаксис документа, внутрішнє посилання на recovery guide та `git diff --check` перевірено. Команди не запускалися автоматично й не змінюють дані.
- **Нові змінні середовища:** немає.

## 2026-09-16 — report-workflow-guide-refresh (завершено)

- **Задача:** синхронізувати документацію з реалізованим workflow від створення звіту до public passport/PDF і зафіксувати межі можливого розширення публічних полів.
- **Змінені файли:** `docs/guides/{current-domain-and-report-workflow,README}.md`, `docs/{architecture,db-schema,local-start,tech_diamant_id,progress}.md`, `README.md`.
- **Результат:** guide тепер описує три кроки wizard, всі поточні групи private-полів, IDC/demo-price межу, ролі, lifecycle і review/issue/void, публічні та виключені поля, code/URL/QR/PDF, reissue/revoke/void і безпечний порядок додавання нових публічних полів. Функціонал public фото/plotting прямо прив’язано до backlog 130. Документація запуску й архітектура також фіксують `ghostMode: false`, щоб кілька локальних вікон не дублювали дії.
- **Перевірки:** внутрішні Markdown-посилання та `git diff --check` перевірено; runtime-код і схема даних не змінювалися.
- **Нові змінні середовища:** немає.

## 2026-09-16 — local-browser-sync-action-isolation (завершено)

- **Задача:** прибрати дублювання дій у кількох локально відкритих вікнах Diamant ID.
- **Змінені файли:** `frontend/gulpfile.js`, `frontend/package.json`, `frontend/tests/local-dev-config.test.mjs`, `docs/progress.md`.
- **Результат:** BrowserSync у `npm start` запускається з `ghostMode: false`; він як і раніше оновлює сторінки після зміни файлів, але більше не дзеркалить кліки, введення чи завантаження між вікнами/вкладками. Тому завантаження PDF, збереження та інші дії виконуються лише у вікні, де їх натиснули.
- **Перевірки:** `npm test` включає окрему regression-перевірку конфігурації `ghostMode: false`.
- **Нові змінні середовища:** немає.

## 2026-09-16 — public-passport-delivery-pdf (завершено)

- **Задача:** завершити передачу виданого публічного паспорта: видимий код, URL/QR lookup і безпечний PDF для замовника.
- **Змінені файли:** `backend/{main,passport_pdf}.py`, `backend/assets/fonts/{DejaVuSans.ttf,DejaVuSans-Bold.ttf,README.md}`, `requirements.txt`, `frontend/src/{pug/pages/{index,report-detail}.pug,scss/_ui-primitives.scss,js/{main.js,modules/{api,report-detail}.js}}`, `tests/api/test_public_passport_pdf.py`, `frontend/tests/{page-dom.test.mjs,e2e/public-passport-delivery.spec.mjs}`, `docs/{architecture,work_plan,progress}.md`, `docs/backlog/{README.md,095-public-passport-delivery-pdf.md (видалено)}`.
- **Результат:** admin для активного опублікованого `issued` report бачить `public_id`, URL, QR та може скопіювати код/посилання і завантажити «Публічний паспорт». `GET /reports/{id}/passport/pdf` лишається admin-only, вимагає саме current valid public URL і будує односторінковий PDF on-demand з того ж allow-list, що й anonymous endpoint: без ціни, коментарів, market status, історії, експерта чи media. PDF містить номер звіту для читання, характеристики, дату дослідження/видачі, QR, URL і код; DejaVu Sans bundled як runtime-asset для українського тексту. Landing приймає лише raw code зі сторінки звіту; пряме публічне посилання та посилання з QR відкривають паспорт напряму. `DR-…` не є публічним ключем. Reissue вимикає PDF зі старим URL, revoke/void закривають нове завантаження.
- **Перевірки:** targeted API/PDF tests, `npm test`, targeted Playwright lookup/download, FastAPI import smoke, rendered PDF visual QA та `git diff --check` — успішно.
- **Нові змінні середовища:** немає. URL для PDF бере поточний browser origin, тому після deploy QR/PDF міститимуть фактичний public origin, а не локальний `localhost`.
- **Обмеження:** PDF не є persisted або юридично незмінним snapshot; відкликання не може забрати вже переданий файл, але одразу робить його QR/URL нечинним. Набір публічних полів лишається явним allow-list і може бути переглянутий окремо; public media як і раніше винесено у 130.

## 2026-09-16 — public-passport-and-qr (завершено)

- **Задача:** реалізувати безпечний публічний паспорт і QR, не відкриваючи private `/reports`, media, ціни чи персональні дані.
- **Змінені файли:** `backend/{crud,main,models,schemas}.py`, `alembic/versions/0005_public_passports.py`, `requirements.txt`, `frontend/src/{pug/pages/{index,passport,report-detail}.pug,scss/_ui-primitives.scss,js/{main.js,modules/{api,public-passport,report-detail}.js}}`, `tests/{api/test_public_passport.py,unit/test_migration_foundation.py}`, `frontend/tests/{auth-and-api,page-dom}.test.mjs`, `frontend/tests/e2e/{public-passport,public-passport-controls,report-detail-confirmation-grades}.spec.mjs`, `scripts/audit-api.mjs`, `docs/{architecture,db-schema,local-start,tech_diamant_id,work_plan,progress}.md`, `docs/{guides/current-domain-and-report-workflow.md,backlog/{README,130-public-passport-media}.md}`.
- **Результат:** `public_passports` зберігає випадковий revocable `public_id`; anonymous `GET /public/passports/{public_id}` віддає лише allow-listed issued projection. Для draft/review/void, відкликаного або вгаданого token повертається однаковий `404`. Лише admin публікує, відкликає або перевипускає посилання; `void` негайно закриває public projection. QR — server-generated SVG лише з валідним URL `passport.html?id=<public_id>`. Public UI не потребує JWT; private detail показує admin controls. Головний пошук явно приймає лише код публічного паспорта, а не внутрішній номер звіту. `Polish`, `Symmetry`, підтверджені Proportions і Final Cut у detail — текстові селекти, наповнені з `diamond_market.grade_mappings`; API і БД зберігають їхні чинні числові коди. Додано `qrcode==8.2` без зовнішнього QR-сервісу.
- **Перевірки:** `python -m pytest` — 23 passed; `npm test` — 13 passed; targeted Playwright public passport — 1 passed; full mock E2E запущено для наявних flows. `git diff --check` — успішно. API regression перевіряє RBAC, allow-list, QR SVG, reissue, revoke і void. Після застосування міграції `npm run audit:api` — 10/10. Додаткові Playwright regression підтвердили: для report `review` admin бачить лише пояснення, без QR і дій публікації; експерт обирає text grades із server mappings, а збереження передає їхні numeric codes.
- **Нові змінні середовища:** немає.
- **MariaDB:** migration `0005_public_passports` застосовано до локальної MariaDB; `alembic current` — `0005_public_passports (head)`. Створено лише таблицю токенів `public_passports`, без дублювання або перерахунку даних звітів.
- **Відкладено окремо:** public media не підтримується навіть для `MediaAsset.is_public`; consent, asset allow-list і окремий content endpoint зафіксовано у [130](./backlog/130-public-passport-media.md).
- **Реалізовано наступним кроком:** передача паспорта замовнику — видимий код, lookup за URL/кодом і server-generated allow-listed PDF — описана в актуальному записі вище.

## 2026-09-16 — legacy-api-retirement (завершено)

- **Задача:** завершити retirement невикористаного `/diamonds/*` після private detail/edit, не змінюючи historical дані.
- **Змінені файли:** `backend/{main,crud,models,schemas}.py`, `frontend/src/js/main.js`, `scripts/audit-api.mjs`, `tests/api/{test_auth_and_experts,test_legacy_api_retirement}.py`, `frontend/{package.json,tests/legacy-api-retirement.test.mjs}`, `docs/{architecture,db-schema,local-start,tech_diamant_id,work_plan,progress}.md`, `docs/{guides/current-domain-and-report-workflow.md,backlog/{README,120-legacy-calculation-and-ml-boundary}.md}`.
- **Результат:** `/diamonds/*`, dead frontend handler, legacy Pydantic/CRUD contracts і випадковий demo `MLService` вилучено. `/reports` є єдиним API для приватних звітів; API-аудитор перевіряє його межу доступу без токена. Historical legacy-колонки та значення `price` лишилися без схеми, міграції чи backfill.
- **Перевірки:** додано API regression на 404 для кожного retired route, перенесено чинні auth/experts перевірки й додано Node guard, що active frontend не містить retired endpoint. `python -m pytest` — 21 passed; `npm test` — 11 passed; full Playwright запуск підтвердив login/dashboard/wizard flows, а targeted detail/edit — 1 passed; `npm run audit:api` — 9/9; `git diff --check` і FastAPI import/route smoke — успішно.
- **Нові змінні середовища:** немає.
- **Обмеження та наступна задача:** `scripts/recalc_grades.py` навмисно не запускався і не переписувався. Нова [120 — Legacy-перерахунок і межа ML](./backlog/120-legacy-calculation-and-ml-boundary.md) має окремо погодити його retire або безпечну versioned replacement з dry-run, scope, audit trail та планом відновлення. Public passport, authoritative pricing/FX і ML не реалізовано.
- **Виявлено поза scope:** read-only audit на локальній відновленій MariaDB отримав `500` від `/statistics/expert-performance`; endpoint вилучено з вузького report/auth audit, а його перевірка й виправлення були винесені у завершену 108 до будь-якого analytics UI.

## 2026-09-16 — report-detail-layout-refinement (завершено)

- **Задача:** вирівняти private detail/edit сторінку з канонічними UI-примітивами та зробити її керованою на mobile.
- **Змінені файли:** `frontend/src/scss/_ui-primitives.scss`, `docs/progress.md`.
- **Результат:** заголовок desktop має узгоджені відступи; form `select` і `textarea` отримали повну ширину, 2px controls та focus-стан; textarea коментаря до lifecycle має достатню висоту. Нижній простір сторінки відділено від footer. На mobile кнопка повернення та detail-дії займають окремі повні рядки; CSS тепер явно приховує кнопки з атрибутом `hidden`, тож одночасно не показуються `Редагувати`, `Зберегти` і `Скасувати`. SVG-маркер select не перезаписується фоном detail-стилю.
- **Перевірки:** `npm run build` — успішно; `npm test` — 10 passed; `git diff --check` — успішно. Вбудований Browser у цій сесії недоступний, тому rendered desktop/mobile smoke виконав користувач у власному браузері.
- **Нові змінні середовища:** немає.
- **Обмеження:** не змінювалися Pug, JavaScript, API, RBAC, дані та тести; відомі Sass `@import` і Browserslist warnings залишилися без змін.

## 2026-09-16 — mariadb-local-recovery (завершено)

- **Задача:** безпечно перевести локальні бази Diamant ID з тимчасово відновленого XAMPP MariaDB у чисту інсталяцію.
- **Змінені файли:** `docs/{local-start,work_plan,progress}.md`, `docs/guides/{README,mariadb-local-recovery}.md`.
- **Результат:** старий пошкоджений `mysql/data` перейменовано в окремий аварійний архів; новий чистий `data` створено зі штатного `mysql/backup` того ж XAMPP. SQL-дампами відновлено `diamond_oltp`, `diamond_market`, `diamond_analytics`, а також `freight_transport`, `freight_transport_secure`, `ship_voyages_db`. Після імпорту створено окремий контрольний дамп Diamant ID з чистого сервера.
- **Перевірки:** чистий MariaDB 10.4.32 стартував без `innodb_force_recovery`, штатно завершився через `mysqladmin shutdown` і пережив повторний старт. `diamond_oltp.diamond_reports` містить 1 001 запис; `alembic_version` — `0004_report_wizard`; `alembic current` з репозиторію підтвердив head; FastAPI імпортується. Ручний smoke frontend: admin увійшов і відкрив новий звіт. Seed, Alembic migration/downgrade та кодова схема не запускалися й не змінювалися.
- **Нові змінні середовища:** немає; зміна host/port після переходу, якщо буде потрібна, лишається приватною зміною `.env`.
- **Обмеження:** `xampp-control.exe` раніше зависав під час закриття; це окрема проблема UI Control Panel і не вплинула на відновлений MariaDB. До її окремої діагностики MariaDB безпечніше запускати та зупиняти консольними командами з guide. Вкладення звітів не входять до SQL-дампів і залишаються відповідальністю окремого filesystem backup.

## 2026-09-16 — report-detail-and-editing (завершено)

- **Задача:** реалізувати захищений private detail/edit звіту, lifecycle UI та повну історію суттєвих змін.
- **Змінені файли:** `backend/{crud,main}.py`, `frontend/src/{pug/pages/report-detail.pug,scss/_ui-primitives.scss,js/{main.js,modules/{api,dashboard,report-detail}.js}}`, `tests/api/test_report_domain.py`, `frontend/tests/{page-dom.test.mjs,e2e/{dashboard,report-detail}.spec.mjs}`, `docs/{architecture,work_plan,progress}.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/backlog/{README.md,080-report-detail-and-editing.md}`.
- **Результат:** dashboard відкриває приватну `/report-detail.html`; owner/admin можуть редагувати лише `draft`, включно з повним normalized stone, examination date, expert confirmation і детальним `market_status`. Сторінка показує системний IDC окремо від expert-confirmed grades, приватні вкладення та append-only history. `PUT /reports/{id}` тепер записує `report_updated`, а lifecycle transition лишається server-side контролюваним; admin не може видати report без підтверджених grades.
- **Перевірки:** `python -m pytest` — 24 passed; `npm test` — 10 passed; цільовий Playwright flow owner edit — 1 passed. Повний `npm run test:e2e` показав успіх login/dashboard/wizard worker-ів до ліміту execution window; новий detail flow підтверджено окремо. `npm run build` і `git diff --check` — успішно.
- **Нові змінні середовища:** немає.
- **Обмеження:** MariaDB/XAMPP не перевірялася і не змінювалася: у користувача є окрема нестабільність MySQL. E2E використовує mock HTTP, а не реальні локальні дані. Друк, public passport, cleanup `/diamonds/*`, admin/profile UI та авторитетні ціни залишаються окремими задачами.

## 2026-09-15 — authoritative-market-data-plan (заплановано)

- **Задача:** зафіксувати окремий шлях від demo-індексу до перевірюваних ринкових довідкових даних і, за потреби, валютних курсів.
- **Змінені файли:** `docs/backlog/{README,100-profile-and-admin-ui,110-authoritative-market-data-and-fx}.md`, `docs/{work_plan,progress}.md`.
- **Рішення:** `6000`, legacy `price` і детермінований прогноз wizard не є ринковою ціною та не записуються до нового звіту як фінансова величина. Нова задача 110 вимагатиме окремо погодити авторитетного провайдера та його умови, валюту/одиницю, provenance, незмінні snapshot-и, ручний admin-flow і лише потім scheduler. Курс валюти розмежовано з котируванням діаманта.
- **Перевірки:** Markdown-посилання та залежності звірені з ADR-002, backlog і work plan; код, MariaDB, seed та зовнішні API не змінювалися.
- **Нові змінні середовища:** немає; можливі provider credentials будуть визначені лише під час реалізації та не потраплять до репозиторію.
- **Обмеження:** конкретний провайдер, ліцензія, базова валюта, спосіб зіставлення 4C і потреба в USD/UAH ще не погоджені; до цього автоматичне оновлення або збереження «ціни» не реалізовуються.

## 2026-09-15 — current-state-reconciliation-audit (завершено)

- **Задача:** звірити фактичний стан коду після 070 з архітектурою, schema/runbook, guide, backlog і тестовими правилами перед стартом 080.
- **Змінені файли:** `.codex/rules/testing.md`, `docs/{architecture,db-schema,local-start,work_plan,progress}.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/backlog/{README,080-report-detail-and-editing,085-legacy-api-retirement}.md`.
- **Результат:** документація тепер фіксує, що dashboard і wizard використовують приватний `/reports`, а `/diamonds/*` є legacy compatibility API. Runbook доведено до Alembic `0004_report_wizard`; workflow описує фактичні RBAC, lifecycle, `examination_date`, server preview, media та межі demo-ціни. Правила тестування приведені у відповідність до чинних pytest/Node/Playwright наборів.
- **Виявлені кодові доробки:** 080 мусить додати `report_updated` event для успішного `PUT /reports/{id}`, private detail/edit UI, явний admin-review/issue/void flow і детальний commercial state. Після 080 задача 085 прибере unreachable legacy frontend handler `/diamonds/*` та зафіксує долю compatibility маршрутів. Ці зміни не виконувалися в аудиті.
- **Перевірки:** статично звірено FastAPI routes, CRUD/RBAC, Pydantic contracts, Alembic revisions, Pug/JS API-виклики, pytest/Node/Playwright набори та Markdown-посилання. `npm run build` — успішно; відомі Sass `@import` і Browserslist warnings залишилися без змін.
- **Нові змінні середовища:** немає.
- **Обмеження:** аудит не запускав MariaDB migration/seed і не змінював runtime-дані. Реальний admin review UI і E2E з живою MariaDB ще відсутні.

## 2026-09-15 — report-creation-wizard (завершено)

- **Задача:** перевести форму «Новий звіт» на трикроковий wizard із приватним контрактом `POST /reports`, серверними довідниками, live IDC preview, валідацією та необов'язковими приватними вкладеннями.
- **Змінені файли:** `backend/{crud,main,models,schemas}.py`, `alembic/versions/0004_report_wizard.py`, `frontend/src/{pug/pages/create-report.pug,scss/{main,_ui-primitives}.scss,js/{main.js,modules/{api,report-wizard}.js}}`, `tests/{api/test_report_domain.py,unit/test_migration_foundation.py}`, `frontend/tests/{auth-and-api,page-dom}.test.mjs`, `frontend/tests/e2e/report-wizard.spec.mjs`, `docs/{architecture,db-schema,work_plan,progress}.md`, `docs/backlog/070-report-creation-wizard.md`.
- **Рішення:** `GET /reports/next-id` показує наступний номер без резервування; остаточний ID призначає `POST /reports`. Додано `examination_date`, geometry-довідники, server-side preview та детермінований `demo_price_usd`. Позначка `d` означає демонстраційний прогноз, а не ринкову, експертну чи продажну ціну; це значення не зберігається у фінансовому контракті звіту. Нова чернетка отримує `market_status=not_for_sale`; керування продажем перенесено до 080. Медіа після створення draft завантажуються через приватний API й необов'язкові.
- **MariaDB:** за погодженням застосовано `0004_report_wizard` до локальної MariaDB. Seed, backfill і downgrade не запускалися.
- **Перевірки:** `python -m pytest tests/api/test_report_domain.py` — 4 passed; `npm test` — 9 passed; `npx playwright test -c playwright.config.mjs tests/e2e/report-wizard.spec.mjs` — 1 passed; `git diff --check`. Playwright мокував API й не змінював MariaDB.
- **Нові змінні середовища:** немає.
- **Ручний smoke:** gemologist успішно створив реальну локальну чернетку через wizard. Контрольний запис свідомо лишається у MariaDB для наступних етапів і буде видалений лише окремо погодженим очищенням даних.
- **Обмеження:** private detail/edit, зміну commercial status, transitions і public passport не реалізовано.

## 2026-09-15 — 060-reports-dashboard (завершено)

- **Задача:** перевести dashboard із mock/legacy `/diamonds/` на робочий приватний список звітів.
- **Змінені файли:** `backend/{main,crud,schemas}.py`, `tests/api/test_report_domain.py`, `frontend/src/{pug/pages/dashboard.pug,js/{main,modules/{api,dashboard}.js},scss/{_variables,_ui-primitives}.scss}`, `frontend/tests/{auth-and-api,page-dom}.test.mjs`, `frontend/tests/e2e/dashboard.spec.mjs`, `DESIGN.md`, `docs/{architecture,work_plan,progress}.md`, `docs/{guides/current-domain-and-report-workflow.md,decisions/002-financial-calculation-contract.md}`, `docs/backlog/{README.md,060-reports-dashboard.md}` (задачу видалено після реалізації).
- **Рішення:** `GET /reports` повертає `{items,total,page,page_size,total_pages}`, обмежує `page_size` до 100, застосовує allow-list сортувань, пошук за `report_id`, швидкий lifecycle-фільтр і `sold=true|false` для двостанового відображення продажу, а в розгорнутій панелі — форму, 4C, діапазони ваги/ціни та дати. Історичний детальний `market_status` не втрачається: «Продано» означає лише `sold`, «Не продано» — всі інші поточні стани (`not_for_sale`, `available`, `reserved`, `withdrawn`). Gemologist бачить лише власні записи й не бачить control вибору експерта; admin бачить усі або одного обраного експерта. Для admin control показується відразу за локальною ідентифікацією, щоб не зсувати макет, але список експертів і остаточна видимість підтверджуються `/users/me` сервером. Dashboard повернуто до table-first вітрини з 4C і двома відокремленими статусами: «Статус звіту» та «Статус продажу». Верхній ряд містить лише обидва статуси, а для admin — ще експерта; усі quick controls мають спільну висоту та стилі input, текстова мітка пошуку візуально прихована. До `767px` «Новий звіт» має ширину внутрішніх control елементів; у tablet-діапазоні 768–900px він лишається компактною кнопкою праворуч. Для ширини 768–900px navigation примусово підпорядкована burger-state, попри legacy desktop media-query. Демо-примітка розташована безпосередньо перед таблицею. Заголовки колонок запускають server-side сортування й показують `▲`/`▼`, дата знов показує час. Пагінація має першу/попередню/наступну/останню сторінки, номер останньої сторінки та mobile-компоновку без зайвих проміжних номерів. Значення legacy `price` demo-набору 2023–2025 показується як `USD … d`; натискання пояснює джерело, дату і межі набору, клік поза popover або `Esc` закриває його. Це не поточне котирування, не ціна продажу і не механізм переоцінки історії. Колонка «Дії» має доступний overflow-control `⋮`, який також закривається кліком поза меню або `Esc`; пункти detail/edit/print вимкнені до задачі 080, а bulk-операції не додані.
- **Перевірки:** `python -m pytest` — 22 passed; `npm test` — 8 passed; `npm run test:e2e` — 2 passed, зокрема dashboard flow через mock HTTP-відповіді; `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** реальна browser-перевірка з локальною MariaDB та 1 000 записів має бути виконана вручну після запуску backend/frontend. Wizard, private detail/edit/print, lifecycle transitions, публічний паспорт і bulk-дії не входять до 060.

## 2026-09-15 — ui-primitives (завершено)

- **Задача:** уніфікувати базові UI-примітиви перед наступними dashboard і wizard-зрізами.
- **Уточнення після visual QA:** прибрано застарілий відступ у dashboard-пошуку після вилучення іконки; desktop-блок ідентичності сесії відокремлено тонкою лінією, а `Увійти` і `Вийти` на mobile мають спільну типографіку та область натискання.
- **Виправлення після ручної перевірки:** historical selector пошуку мав вищу специфічність, тому зберігав зайву внутрішню рамку; нове правило перевизначає його точним селектором. Пункти mobile-навігації `Увійти` і `Вийти` тепер мають однакову фактичну висоту, відступи та шрифт.
- **Остаточне UI-уточнення:** динамічні дії mock-таблиці застосовують текстові `table-action` замість emoji-іконок; inputs і selects у розгорнутих фільтрах також мають `2px`, попри історичний локальний селектор.
- **Змінені файли:** `frontend/src/{scss/{main,_ui-primitives}.scss,js/main.js,pug/pages/{dashboard,create-report}.pug}`, `frontend/tests/page-dom.test.mjs`, `DESIGN.md`, `docs/{work_plan,progress}.md`, `docs/backlog/{README.md,055-ui-primitives.md}` (задачу видалено після реалізації).
- **Рішення:** `_ui-primitives.scss` є канонічним останнім шаром повторно використовуваних control-стилів. Великі поверхні flat (`0`), кнопки/inputs/select/badges/pagination — `2px`; кнопки мають лише текст. Header, footer і session-actions мають спільні hover/focus правила. Username — темний identity-block із нейтральною роллю; desktop розміщує його перед синім `Вийти`, mobile показує ім’я поруч із burger, повну роль — усередині меню. Admin не маркується червоним лише через роль.
- **Перевірки:** `npm run build`; `npm test` — 7 passed; browser QA через Playwright fallback (вбудований Browser недоступний): desktop landing `1440×900`, desktop create-report авторизованого expert, mobile dashboard menu `390×844`; `git diff --check`.
- **Нові змінні середовища:** немає.
- **Обмеження:** task не переносить dashboard/wizard на `/reports`, не прибирає legacy mock rows або hardcoded mappings, не реалізує нові функції таблиці чи pagination. Ці межі лишаються задачами 060 і 070.

## 2026-09-15 — media-assets (завершено)

- **Задача:** реалізувати приватні вкладення звітів: локальне сховище, метадані, API, RBAC і UI fallback.
- **Змінені файли:** `backend/{config,media_storage,models,schemas,crud,main}.py`, `alembic/versions/0003_media_assets.py`, `.env.example`, `.gitignore`, `frontend/src/{pug/pages/create-report.pug,scss/main.scss,js/{main.js,modules/api.js},img/*.svg}`, `tests/{api/test_report_media.py,unit/test_migration_foundation.py}`, `frontend/tests/page-dom.test.mjs`, `docs/{architecture,db-schema,local-start,work_plan,progress}.md`, `docs/backlog/{README.md,050-media-assets.md}` (задачу видалено після реалізації).
- **Рішення:** `media_assets` зберігає тип, server-generated storage key, MIME, розмір, SHA-256, автора, дату та `is_public=false`. Файли зберігаються поза БД і Git у `storage/reports/<report-id>/`; FastAPI не відкриває каталог статично. Доступ на upload/list/content/delete перевіряється server-side для owner/admin, а зміни дозволені лише у `draft`. JPEG/PNG/WebP обмежені 10 MB, PDF — 20 MB; declared MIME звіряється з сигнатурою файла. `plotting_image` і `real_image` legacy-звітів не перенесено, бо це непідтверджені placeholder-шляхи.
- **MariaDB:** за погодженням застосовано `0003_media_assets` поверх `0002_report_core`; `alembic current` підтвердив `0003_media_assets (head)`, таблиця `diamond_oltp.media_assets` існує. Seed, backfill і downgrade не запускалися.
- **Перевірки:** `alembic upgrade head --sql`; `python -m pytest` — 21 passed; import FastAPI; `npm run build`; `npm test` — 6 passed; `npm run test:e2e` — 1 passed; `git diff --check`. API-тести використовують SQLite і temporary storage, не XAMPP.
- **Нові змінні середовища:** `MEDIA_STORAGE_PATH` — необов’язковий абсолютний шлях до приватного storage; за відсутності застосовується gitignored `storage/reports`.
- **Обмеження:** UI поки підключений до compatibility create-form; task 070 переведе майстер на новий `/reports` контракт. `is_public` не відкриває файли і не створює public URL — це задача 090. Production object storage, антивірус/асинхронна обробка та видалення orphan-файлів — окреме hardening після локального MVP.

## 2026-09-15 — database-schema-documentation (завершено)

- **Задача:** створити єдину фактичну карту локальної MariaDB-схеми Diamant ID після `0002_report_core`.
- **Змінені файли:** `docs/db-schema.md`, `docs/architecture.md`, `docs/progress.md`.
- **Результат:** описано три логічні MariaDB databases, контрольовані значення, зв’язки, ключі, compatibility-межі `diamond_reports`, фінансовий контракт, індекси/unique constraints і Alembic revisions. Документ не містить секретів, SQL для ручної зміни даних або інструкцій destructive repair.
- **Перевірки:** статично звірено `backend/models.py`, `0001_initial_schema`, `0002_report_core`; read-only підтверджено `0002_report_core`, 1 000 reports/stones/events та стан `draft` у локальній MariaDB; `git diff --check` — успішно.
- **Нові змінні середовища:** немає.

## 2026-09-14 — report-core-and-reference-data (завершено)

- **Задача:** реалізувати ядро звіту, нормалізовані дані каменю, lifecycle, server reference data та безпечне перенесення чинної локальної MariaDB.
- **Змінені файли:** `backend/{models,schemas,crud,main}.py`, `alembic/versions/0002_report_core_and_reference_data.py`, `tests/{api/test_report_domain.py,unit/test_migration_foundation.py}`, `docs/{architecture,local-start,work_plan,progress}.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/decisions/003-report-core-migration-plan.md`, `docs/backlog/{README.md,040-report-core-and-reference-data.md}` (задачу видалено після реалізації).
- **Рішення:** введено `Stone → DiamondReport → ReportEvent`; legacy `/diamonds/*` лишається compatibility API до UI-зрізів, а новий `/reports` є приватним. `gemologist` створює власні draft, admin не створює первинні звіти та керує `review → draft/issued/void`. Системні grades відокремлено від експертного підтвердження; `issued` потребує явних expert grades. `StoneValuation` не отримує legacy `price` автоматично.
- **MariaDB:** застосовано `0002_report_core`; `alembic current` підтвердив head. Backfill створив 1 000 `Stone`, 1 000 `ReportEvent` і залишив усі 1 000 reports у `draft`; 690 origin перенесено як `lab_grown`, 44 як `natural`, 266 з legacy-кодами `2/3` — як `unknown`. Створено 30 текстових server reference values. Нічого не видалено, seed/downgrade не запускалися.
- **Перевірки:** `alembic upgrade head --sql`; `python -m pytest` — 19 passed; `alembic history`; MariaDB counts/status/origin checks; тимчасовий Uvicorn smoke на `:8001` підтвердив OpenAPI-маршрути `/reports`, `/reports/{report_id}/transitions`, `/reference-values` і `401` для анонімного `/reports`. `git diff --check` — успішний.
- **Нові змінні середовища:** немає.
- **Обмеження:** frontend поки не використовує `/reports`; міграція не створює `MediaAsset`, Sale або PublicPassport. Авторитетні ринкові ціни, scheduler та ML залишаються окремими задачами; поточний `price` — legacy unclassified value.

## 2026-09-14 — financial-calculation-rules (завершено)

- **Задача:** інвентаризувати поточні ціни, market-дані й demo-ML та зафіксувати фінансовий контракт до зміни ядра звіту.
- **Змінені файли:** `docs/decisions/002-financial-calculation-contract.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/backlog/{README.md,037-financial-calculation-rules.md}` (задачу видалено з активного backlog), `docs/work_plan.md`, `docs/progress.md`.
- **Рішення:** `price` — legacy-значення без автоматичного перенесення; `6000` — технічний demo-індекс без підтверджених валюти, одиниці та джерела; demo-евристика не є ML-моделлю чи ринковою/експертною ціною. Цільові `market_reference`, `system_prediction`, `expert_appraisal`, `asking_price` і `sale_price` мають бути окремими величинами в 040, із `Decimal`/`Numeric`, метаданими й погодженою міграцією.
- **Перевірки:** статичний аудит моделей, Pydantic-схем, CRUD, API, seed, wizard, dashboard і наявних тестів; перевірка внутрішніх Markdown-посилань та `git diff --check`. Runtime- і DB-тести не запускалися, бо код, залежності, конфігурація й схема не змінювалися.
- **Нові змінні середовища:** немає.

## 2026-09-14 — admin-report-rbac (завершено)

- **Задача:** закрити server-side розбіжність із погодженою роллю admin: admin не створює первинні експертні звіти.
- **Змінені файли:** `backend/main.py`, `frontend/src/{js/main.js,js/modules/auth.js,pug/pages/{dashboard,create-report}.pug,scss/_product-ux.scss}`, `tests/api/test_admin_report_rbac.py`, `docs/backlog/README.md`, `docs/backlog/035-admin-report-rbac.md` (видалено після реалізації), `docs/work_plan.md`, `docs/progress.md`.
- **Рішення:** `POST /diamonds/` після JWT-автентифікації перевіряє роль на сервері та приймає створення лише від `gemologist`; admin отримує контрольований `403`. UI-приховування «Новий звіт» більше не є єдиним бар’єром: admin не бачить його в header і на dashboard, а прямий перехід на `create-report.html` повертає на `dashboard.html`. Обидві наявні приватні сторінки (`dashboard.html`, `create-report.html`) спершу приховані й відкриваються лише після локальної перевірки сесії; гість одразу переходить на `login.html`. Серверний `401` очищає локальну сесію й також повертає на login. `logout` приймає маршрут лише як рядок, тому click-подія не може стати помилковим URL. Для dashboard CTA додано scoped CSS-правило, щоб `[hidden]` не перекривався базовим `.btn { display: inline-flex; }`.
- **Перевірки:** `python -m pytest` — 17 passed; smoke-import `from backend.main import app` — успішний; `npm test` — build і 5 Node/jsdom перевірок passed; `npm run test:e2e` — 1 Playwright login smoke passed; `git diff --check` — успішний. Вбудований Browser був заявлений у сесії, але підключення повернуло `No browser is available`; Playwright використано як fallback. Автоматичний browser-flow саме для admin dashboard і guest redirect відсутній, тому приховання CTA та `dashboard.html → login.html` потрібно один раз вручну звірити після локального `npm start`. Є наявні попередження SQLAlchemy 2 (`declarative_base`) і Pydantic 2 (`class Config`, `.dict()`), а також Sass `@import` і застарілі Browserslist data; їх не змінювали в межах RBAC-задачі.
- **Нові змінні середовища:** немає.

## 2026-09-14 — finance-and-ui-primitives-plan (завершено)

- **Задача:** запланувати правила точних фінансових розрахунків і рефакторинг UI-примітивів до реалізації ядра звіту, dashboard та wizard.
- **Змінені файли:** `.codex/rules/local-finance.md`, `AGENTS.md`, `docs/backlog/{README,037-financial-calculation-rules,055-ui-primitives}.md`, `docs/work_plan.md`, `docs/progress.md`.
- **Рішення:** 037 виконується після server-side RBAC і перед ядром звіту; вона відокремлює ринкову ціну, системний прогноз, експертну оцінку та опціональний факт продажу. 055 виконується після ядра звіту й перед dashboard/wizard, незалежно від медіа; це малий Pug/SCSS-шар повторно використовуваних елементів, а не заміна технологічного стека чи редизайн.
- **Перевірки:** `git diff --check`; перевірка посилань backlog і порядку в `work_plan.md`. Runtime-, API- та frontend-тести не запускалися, бо код, залежності й конфігурація не змінювалися.
- **Нові змінні середовища:** немає.

## 2026-09-14 — hero-text-edge-fade (завершено)

- **Задача:** повернути погоджений локальний білий edge-fade під текстом desktop hero.
- **Змінені файли:** `frontend/src/scss/_product-ux.scss`, `docs/guides/product-ux-foundation.md`, `docs/progress.md`.
- **Рішення:** псевдоелемент hero створює білий перехід лише зліва направо на desktop: текст має стабільний контраст, а діамант і правий край фото не тонуються. На mobile градієнт вимкнений, бо фото та текст розташовані окремими блоками.
- **Перевірки:** `npm run build`, `npm test` (5 passed), `npm run test:e2e` (1 passed), `git diff --check`; Playwright screenshots hero на `1440×900` і `390×844`. Вбудований Browser у цій сесії недоступний, застосовано Playwright fallback.
- **Нові змінні середовища:** немає.

## 2026-09-14 — product-ux-surface-polish (завершено)

- **Задача:** завершити точкове візуальне узгодження hero, mobile-header і footer після UX-рев’ю.
- **Змінені файли:** `frontend/src/scss/_product-ux.scss`, `docs/progress.md`.
- **Рішення:** desktop hero починається після відступу `3rem` від header і не має скруглених кутів; на mobile між username та burger є відступ `1rem`. Footer синхронізовано з header за white surface, border, нейтральним текстом, sapphire hover і видимими focus-станами.
- **Перевірки:** `npm run build`, `npm test` (5 passed), `npm run test:e2e` (1 passed), `git diff --check`; Playwright-візуальна перевірка desktop full-page і mobile авторизованого header. Вбудований Browser у цій сесії недоступний, застосовано Playwright fallback.
- **Нові змінні середовища:** немає.

## 2026-09-14 — product-ux-header-access-refinement (завершено)

- **Задача:** закрити UX-уточнення header: mobile-вхід для гостя, видимий username авторизованого користувача та узгоджені desktop-дії сесії.
- **Змінені файли:** `frontend/src/pug/layout/main.pug`, `frontend/src/js/main.js`, `frontend/src/scss/_product-ux.scss`, `docs/guides/product-ux-foundation.md`, `docs/progress.md`.
- **Рішення:** у mobile burger-меню гостя є `Увійти`; для авторизованого користувача username розташований перед burger-кнопкою. На desktop `Увійти` і `Вийти` є однаково оформленими текстовими діями, відокремленими лінією від основного меню. Для desktop landing додано верхній відступ `1.5rem` між header і hero.
- **Перевірки:** `npm run build`, `npm test` (5 passed), `npm run test:e2e` (1 passed), `git diff --check`; Playwright screenshot на `390×844` для guest-menu та gemologist-header, `1440×900` для desktop landing. Вбудований Browser у цій сесії недоступний, застосовано Playwright fallback.
- **Нові змінні середовища:** немає.

## 2026-09-14 — product-ux-navigation-refinement (завершено)

- **Задача:** уточнити погоджену навігацію ролей, вирівнювання desktop-header, mobile-меню та поведінку hero після візуального рев’ю.
- **Змінені файли:** `frontend/src/js/main.js`, `frontend/src/scss/_product-ux.scss`, `docs/guides/product-ux-foundation.md`, `docs/backlog/{README,035-admin-report-rbac.md}`, `docs/work_plan.md`, `docs/progress.md`.
- **Рішення:** гість бачить `Перевірити паспорт` і кнопку `Увійти`; gemologist — `Всі звіти`, `Новий звіт`, `Профіль` і окрему дію `Вийти`; admin — `Всі звіти`, `Експерти`, `Довідники`, `Аналітика`, `Профіль` і `Вийти`, без створення звітів. На mobile в burger-меню видно ім’я користувача та одну дію виходу, без дублювання профілю.
- **Перевірки:** `npm run build`, `npm test` (5 passed), `npm run test:e2e` (1 passed), `git diff --check`; Playwright-візуальна перевірка на `1440×900` та `390×844` для гостя, gemologist і admin. Вбудований Browser у цій сесії недоступний, застосовано Playwright fallback.
- **Нові змінні середовища:** немає.
- **Обмеження:** приховання пункту «Новий звіт» для admin є лише UI-логікою; чинний `POST /diamonds/` ще не забороняє цю дію на сервері. Це зафіксовано як [035 — admin report RBAC](./backlog/035-admin-report-rbac.md).

## 2026-09-14 — product-ux-visual-foundation (завершено)

- **Задача:** реалізувати погоджену UX і візуальну основу Diamant ID до наступних вертикальних зрізів звітів, медіа та admin UI.
- **Змінені файли:** `frontend/src/pug/{layout/main,pages/index}.pug`, `frontend/src/scss/{_variables,_product-ux,main}.scss`, `frontend/src/js/main.js`, `frontend/gulpfile.js`, `frontend/src/img/diamond-inspection-hero.png`, `docs/guides/product-ux-foundation.md`, `docs/work_plan.md`, `docs/backlog/{README,030-product-ux-and-visual-foundation.md}`.
- **Рішення:** desktop-логотип лишається зліва, а навігація — праворуч перед профілем/виходом; public landing використовує один предметний macro-asset каменю. Dashboard залишається table-first, wizard — двоколонковим на desktop; фіолетовий legacy badge замінено холодним синім. Публічна навігація створюється через DOM API, а назва користувача екранується перед legacy template.
- **Asset pipeline:** для Gulp 5 додано `encoding: false` під час копіювання `src/img`, бо UTF-8 decoding пошкоджував байти PNG; перевірено ідентичність SHA-256 source/dist.
- **Перевірки:** `npm run build`, `npm test` (5 passed), `npm run test:e2e` (1 passed), `git diff --check`; Playwright screenshot перевірив landing на `1440×900` та `390×844`, а dashboard і create-report на desktop. Вбудований Browser у цій сесії був недоступний, тому застосовано Playwright fallback.
- **Нові змінні середовища:** немає.
- **Обмеження:** API-фільтри, публічний паспорт/QR, profile/admin UI та реальні upload/media не імітуються в цьому UI-шарі; вони залишаються окремими backlog-зрізами.

## 2026-09-14 — migration-foundation (завершено)

- **Задача:** ввести Alembic для трьох локальних MariaDB databases до зміни моделі звіту.
- **Змінені файли:** `alembic.ini`, `alembic/`, `requirements.txt`, `backend/config.py`, `scripts/{bootstrap_mariadb_databases,seed_db}.py`, `tests/unit/test_migration_foundation.py`, `AGENTS.md`, `docs/{architecture,local-start,work_plan,progress}.md`, `docs/backlog/020-migration-foundation.md` (видалено).
- **Рішення:** Alembic веде таблиці, `seed_db.py` після руйнівного створення databases викликає `upgrade head` замість `create_all`; окремий bootstrap створює лише відсутні databases. Для autogenerate/check `diamond_oltp` нормалізується як default MariaDB schema лише в comparison metadata; ORM-моделі та migration SQL зберігають явні схеми.
- **MariaDB-перевірка:** поточну БД позначено `0001_initial_schema`; `alembic check` — без нових upgrade-операцій. Тимчасова revision створила лише `_alembic_migration_smoke`, rollback видалив її (`True → False`) і повернув ревізію до `0001`; тестовий migration-файл не збережено.
- **Перевірки:** `alembic upgrade head --sql`, `alembic history`, `alembic check`, `alembic current`, `pytest` (15 passed), `pip check`, Python compileall і `git diff --check`. Залишилися відомі warnings SQLAlchemy/Pydantic, винесені окремим пунктом плану; targeted повторний запуск migration-тестів також показав не блокувальний `PytestCacheWarning` через права на локальний `.pytest_cache`.
- **Нові змінні середовища:** немає.

## 2026-09-14 — current-domain-and-workflow-guide (завершено)

- **Задача:** започаткувати `docs/guides/` і описати реалізований доменний workflow Diamant ID без підміни його цільовою моделлю.
- **Змінені файли:** `docs/guides/README.md`, `docs/guides/current-domain-and-report-workflow.md`, `docs/work_plan.md`, `docs/progress.md`.
- **Результат:** guide фіксує фактичні ролі, JWT, життєвий цикл поточного запису звіту, IDC-розрахунок, demo-price, продаж, dashboard, медіа та публічні API-межі; ADR-001 і backlog явно позначені як майбутній стан.
- **Перевірки:** статично звірено `backend/main.py`, `models.py`, `schemas.py`, `crud.py`, frontend dashboard/create-report; перевірено Markdown-посилання й `git diff --check`. Runtime, seed і тести не запускалися, бо зміни лише документаційні.
- **Нові змінні середовища:** немає.

## 2026-09-14 — report-domain-contract (завершено)

- **Задача:** зафіксувати цільовий доменний контракт локального MVP до зміни ORM, MariaDB-схеми, API або UI.
- **Змінені файли:** `docs/decisions/001-report-domain-contract.md`, `docs/backlog/README.md`, `docs/backlog/010-report-domain-contract.md` (видалено), `docs/work_plan.md`, `docs/progress.md`.
- **Рішення:** камінь, звіт, продаж, медіа й public passport — окремі сутності; один камінь може мати кілька звітів. Gemologist веде власні `draft` і передає в `review`; лише admin видає (`issued`) або відкликає (`void`). Продаж не змішується з цінами оцінки/прогнозу. Public passport не показує цін, персональних або внутрішніх даних і доступний лише для опублікованого `issued`.
- **Backfill:** поточні записи стають непублічними `draft`; старий `price` не класифікується автоматично, `stone_origin` переноситься лише як preliminary, а legacy-шляхи до файлів не стають медіа без перевірки фізичних файлів.
- **Перевірки:** статичне рев’ю `backend/models.py`, `schemas.py`, `crud.py`, поточної форми створення та правил MariaDB; `git diff --check`. MariaDB, seed, міграції, API і тести не запускалися — ця задача не змінює runtime.
- **Нові змінні середовища:** немає.

## 2026-09-14 — local-mvp-backlog (завершено)

- **Задача:** деталізувати погоджений етап `local-mvp-completion` без зміни runtime-коду: розділити roadmap і активний backlog для наступних задач.
- **Змінені файли:** `docs/work_plan.md`, `docs/backlog/README.md`, `docs/backlog/{010…100}-*.md`, `docs/progress.md`.
- **Рішення:** `work_plan.md` лишається короткою картою етапів; `docs/backlog/` містить лише активні детальні задачі. Після реалізації файл активної задачі видаляється, а результат фіксується у цьому журналі, тематичній документації та merge-коміті.
- **Зафіксований scope MVP:** контракт звіту, Alembic для MariaDB, UX/редизайн, ядро звіту, медіа, dashboard, майстер, private detail/edit, public passport/QR, profile/admin UI. Продаж відокремлено від експертної й прогнозної ціни; публічний паспорт доступний лише для `issued`-звіту з увімкненою публікацією.
- **Перевірки:** перевірено внутрішні Markdown-посилання та `git diff --check`; runtime, seed і тестові набори не запускалися, бо зміни лише документаційні.
- **Нові змінні середовища:** немає.

## 2026-09-14 — testing-foundation (завершено)

- **Задача:** створити ізольований автоматизований test-контур для backend, frontend і браузера без доступу до локальних MariaDB-даних.
- **Змінені файли:** `pytest.ini`, `tests/`, `requirements.txt`, `frontend/tests/`, `frontend/playwright.config.mjs`, `frontend/package*.json`, `.gitignore`, `AGENTS.md`, `docs/{architecture,local-start,work_plan,progress}.md`.
- **Рішення:** API/integration-тести використовують SQLite у пам’яті з `schema_translate_map`, тому не запускають seed і не підключаються до XAMPP; JS-модулі перевіряє native Node test runner, розмітку — jsdom, browser smoke — Playwright із тимчасовим BrowserSync.
- **Покриття:** IDC boundaries/final cut, детермінований ML-прогноз, login/401, `/experts/`, створення/видалення звіту, owner/admin RBAC, 403/404/422, JS auth/API-модулі та login DOM/browser smoke.
- **Перевірки:** `pytest --cov=backend` — 13 passed, 73%; `npm test` — 5 passed; `npm run test:e2e` — 1 passed; `git diff --check` пройдено. Залишилися не блокувальні warnings SQLAlchemy/Pydantic і `caniuse-lite`; їх внесено в backlog, автоматичні оновлення залежностей не застосовувалися.

## 2026-09-14 — report-api-correctness (завершено)

- **Задача:** виправити API звітів без зміни UI: список експертів, створення, RBAC редагування, 404, response-контракт і CRUD-дублікат.
- **Змінені файли:** `backend/main.py`, `backend/crud.py`, `backend/schemas.py`, `docs/work_plan.md`, `docs/api-mvp-audit.md`, `docs/progress.md`.
- **Результат:** `/experts/` повертає список; створення записує `evaluation_time_sec` (5–40 хвилин у секундах); звіт редагує тільки власник або admin; update/delete мають 404 для відсутнього звіту; dashboard отримує `shape` і `cut_grade`; `crud.get_diamonds()` вилучено.
- **Перевірки:** `compileall`, import/OpenAPI-контракт, ізольований smoke створення й RBAC/404 без MariaDB-мутацій, `npm run build` та локальний read-only `npm run audit:api` — 10/10 пройдено. `caniuse-lite` лише попереджає про застарілий довідник браузерів.

## 2026-09-14 — secure-local-foundation (завершено)

- **Задача:** безпечна локальна конфігурація, bcrypt seed, єдиний seed і формалізація `diamond_analytics.ml_results` без руйнівного запуску.
- **Змінені файли:** `backend/config.py`, `backend/database.py`, `backend/security.py`, `backend/models.py`, `scripts/seed_db.py`, `.env.example`, `.gitignore`, `requirements.txt`, документація; `scripts/seed_db-start.py` вилучено як застарілий і несумісний.
- **Рішення:** `ml_results` зберігається як порожній зарезервований шар до окремої задачі API/ML; seed перестворює всі три локальні схеми.
- **Перевірки:** `passlib 1.7.4` несумісний з установленим `bcrypt 5`, тому код перейшов на прямий `bcrypt`; `compileall`, імпорт FastAPI та `MlResult`, bcrypt hash/verify і seed preflight без даних успішні; тимчасовий FastAPI `:8002` пройшов `npm run audit:api` 10/10, `npm run build` успішний. Руйнівний clean seed, login і мутації БД не запускалися; тимчасовий сервер зупинено.

## 2026-09-14 — api-and-mvp-audit (завершено)

- **Задача:** провести аудит усіх API-маршрутів, auth/RBAC, frontend ↔ API, MariaDB-схеми та seed без зміни даних; оновити план робіт рішенням для кожного endpoint-а.
- **Змінені файли:** `docs/api-mvp-audit.md`, `docs/work_plan.md`, `docs/progress.md`.
- **Результат:** зафіксовано статус і дію для всіх OpenAPI маршрутів, критичні дефекти створення звіту/RBAC, UI-розбіжності, legacy seed і schema drift `diamond_analytics.ml_results`; повних API-дублікатів не знайдено.
- **Перевірки:** статичний аналіз backend/frontend/seed; read-only інспекція MariaDB; `npm run audit:api` — 6/10 на вже відкритому `:8000` (DB-маршрути зависли) та 10/10 на тимчасовому чистому FastAPI `:8002`; тимчасовий сервер зупинено. POST/PUT/DELETE, login, seed, SQL-мутації та E2E не запускалися.

## 2026-09-13 — mcp-guidance (завершено)

- **Задача:** актуалізувати правила MCP в `AGENTS.md`, щоб вони не покладалися на статичний список серверів із іншого середовища.
- **Змінені файли:** `AGENTS.md`, `docs/progress.md`.
- **Результат:** джерелом істини визначено доступні інструменти активної сесії; `codex mcp list` залишено необов’язковою перевіркою за наявності налаштованого CLI; додано межі використання MCP і зовнішніх дій.
- **Перевірки:** `codex mcp list` у поточному shell не запускається через відсутній доступний CLI home/CODEX_HOME; це зафіксовано як обмеження середовища, без зміни глобальної конфігурації. `git diff --check` успішний.

## 2026-09-13 — technical-specification (завершено)

- **Задача:** створити технічний опис Diamant ID у стилі `tech_saas.md` з Convertly Hub, але за фактичним стеком і планами Diamant ID.
- **Змінені файли:** `docs/tech_diamant_id.md`, `docs/progress.md`.
- **Результат:** зафіксовано можливості локального MVP, стек, локальну інфраструктуру, API і дані, політику безпеки, межі готовності та окремий планований PostgreSQL/deploy-контур.
- **Перевірки:** звірено з `docs/architecture.md`, `docs/local-start.md`, `docs/work_plan.md`, кодом backend/frontend і наданим прикладом; внутрішні посилання й `git diff --check` успішні.

## 2026-09-13 — architecture-refresh (завершено)

- **Задача:** переписати `docs/architecture.md` у розгорнутому стилі прикладу Convertly Hub, спираючись на фактичний код Diamant ID.
- **Змінені файли:** `docs/architecture.md`, `docs/progress.md`.
- **Результат:** описано компоненти, потоки даних, структуру папок, локальний runtime, API/JWT/RBAC, MariaDB-схеми, IDC і демо-ML, межі реалізації та майбутній PostgreSQL/deploy-контур; реалізований стан відокремлено від планів.
- **Перевірки:** вручну звірено backend, seed, Gulp, frontend API-модулі та локальний runbook; `git diff --check` успішний.

## 2026-09-13 — local-api-audit (завершено)

- **Задача:** адаптувати успадкований Node.js API-аудитор під локальний FastAPI Diamant ID і додати команду запуску та документацію.
- **Змінені файли:** `scripts/audit-api.mjs`, `frontend/package.json`, `.gitignore`, `.codex/skills/api-response-auditor/SKILL.md`, `AGENTS.md`, `docs/progress.md`.
- **Межі:** лише `localhost`/`127.0.0.1` через HTTP; GET та CORS preflight. Скрипт не виконує login, POST, PUT, DELETE, seed або запити з токеном.
- **Перевірки:** `node --check scripts/audit-api.mjs` успішний; `npm run audit:api` проти тимчасового FastAPI на `127.0.0.1:8002` і стандартного локального API на `127.0.0.1:8000` — 10/10 перевірок пройдено; віддалений URL відхиляється до виконання запитів; `git diff --check` успішний.
- **Нові змінні середовища:** опційна `API_AUDIT_BASE_URL` тільки для іншого локального порту.

## 2026-09-13 — agent-guidance-audit (завершено)

- **Задача:** повторно дослідити стек Diamant ID, звірити rules і skills зі структурою Convertly Hub та оновити інструкції агента без перенесення чужих технологічних припущень.
- **Змінені файли:** `AGENTS.md`, `.codex/rules/{python-backend,frontend,database,security,testing,verification,local-architecture,local-quality-and-performance}.md`, `.codex/skills/{api-response-auditor,postgres-patterns,frontend-patterns,diamond-domain-rules,python-patterns,python-testing,database-reviewer,database-migrations,security-review,web-performance}/SKILL.md`, `docs/progress.md`.
- **Результат аудиту:** підтверджено стек FastAPI + SQLAlchemy 2 + MariaDB/XAMPP, Pydantic і JWT; Gulp 5 + Pug + SCSS + vanilla JavaScript + BrowserSync. React, Next.js, Prisma, їхні hooks і правила не застосовні. Автоматичного `audit:api` скрипта та test suite немає.
- **Рішення:** додано правила архітектури й якості/продуктивності, skills `frontend-patterns` і `diamond-domain-rules`, актуалізовано API-аудит і PostgreSQL-патерни для SQLAlchemy. Кожен ключовий skill містить контекст, межі, порядок роботи й очікуваний результат без чужих React/Prisma-припущень. Приклад `.codex/convertly-hub` лишено недоторканим і не зроблено частиною канонічних інструкцій Diamant ID.
- **Перевірки:** структура репозиторію, `README.md`, `docs/architecture.md`, Python- і Node-залежності, Gulp-конфігурація та імпорти коду звірені читанням і пошуком; імпорт `backend.main:app` і `npm run build` успішні. Усі 11 локальних skills проходять `skill-creator/scripts/quick_validate.py` у UTF-8 режимі; `git diff --check` успішний. `caniuse-lite` повідомляє про застарілу базу браузерів, але це не блокує збірку.
- **Нові змінні середовища:** немає.

## 2026-09-13 — login-cors-fix (завершено)

- **Задача:** усунути блокування входу в браузері, коли BrowserSync запускається не на порту `3000`.
- **Змінені файли:** `backend/main.py`, `frontend/src/pug/pages/login.pug`, `docs/local-start.md`, `docs/progress.md`.
- **Результат:** CORS дозволяє лише локальні origins `localhost` або `127.0.0.1` з номером порту; браузер отримує заголовок `Access-Control-Allow-Origin` для `http://localhost:3004`. Поля входу мають `autocomplete="username"` і `autocomplete="current-password"`.
- **Перевірки:** імпорт `backend.main:app` успішний; `npm run build` успішний; CORS preflight `OPTIONS /token` з origin `http://localhost:3004` повертає 200 і коректний `Access-Control-Allow-Origin`; `git diff --check` успішний.
- **Нові змінні середовища:** немає.

## 2026-09-13 — runtime-modernization (завершено)

- **Задача:** перевірити локальний запуск на актуальних Python і Node.js, MariaDB, FastAPI та Gulp без руйнівного seed.
- **Змінені файли:** `docs/local-start.md`, `docs/progress.md`.
- **Перевірки:** Python 3.13.7, Node.js 24.18.0, npm 12.0.1; `pip check` успішний; підключення SQLAlchemy до MariaDB 10.4.32 / `diamond_oltp` успішне; FastAPI `GET /` — 200; BrowserSync `GET /` на `localhost:3000` — 200; `npm run build` успішний. Після відтворення `.venv` перевірено `uvicorn 0.40.0` і `GET /` через звичайний launcher — 200.
- **Рішення:** залежності не оновлювалися, бо несумісності не виявлено. Віртуальне середовище відтворено, оскільки launcher `uvicorn` містив шлях до попереднього розташування проєкту. `caniuse-lite` повідомляє про застарілі browser data, але це не блокує запуск і не потребує зміни lockfile в цій задачі.
- **Нові змінні середовища:** немає.

## 2026-09-13 — agent-project-foundation (завершено)

- **Задача:** адаптувати правила агента, skills і документацію під Diamant ID; провести первинний аудит та сформувати актуальний план.
- **Змінені файли:** `AGENTS.md`, `DESIGN.md`, `.codex/rules/*`, `.codex/skills/python-*`, `docs/{architecture,local-start,work_plan,progress}.md`.
- **Перевірки до змін:** `.venv` Python 3.13.7; імпорт `backend.main:app` успішний; `frontend npm run build` успішний. `caniuse-lite` повідомляє про застарілу базу браузерів.
- **Відомі обмеження:** інтеграційний запуск із MariaDB, тестів і deployment ще не виконано. Технічні нотатки з DOCX прочитано та відображено у `docs/work_plan.md`.
- **Нові змінні середовища:** немає.
- **Git:** зміни підготовлено до коміту й злиття в `local-dev`; `main` навмисно не змінюється.

## 2026-09-13 — структура DESIGN і AGENTS

- **Задача:** узгодити структуру `DESIGN.md` і `AGENTS.md` із шаблоном Convertly Hub, не переносячи його технологічні припущення.
- **Змінені файли:** `DESIGN.md`, `AGENTS.md`, `docs/progress.md`.
- **Результат:** `DESIGN.md` містить повний набір секцій design system, прив’язаних до чинних SCSS-токенів Diamant ID. `AGENTS.md` містить повний життєвий цикл задач, локальні skills, MCP, команди й явний стан відсутньої тестової інфраструктури.
- **Перевірки:** структура Markdown і відповідність названим SCSS-токенам перевірені пошуком у репозиторії.
- **Нові змінні середовища:** немає.

---
