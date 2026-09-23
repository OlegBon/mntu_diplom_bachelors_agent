# Аудит API та локального MVP Diamant ID

> **Актуалізовано:** 23 вересня 2026. Перший аудит від 14 вересня нижче
> збережено як історичний доказ стану до послідовних задач 020–108. Поточним
> джерелом контракту є `docs/architecture.md`, а безпечний runtime smoke —
> `scripts/audit-api.mjs`.

## Поточний стан

- Private workflow працює через `/reports`; legacy `/diamonds/*` вилучено.
  Звіт має owner/admin RBAC, lifecycle `draft → review → issued/void`, private
  detail/edit, media та append-only history.
- Public passport, QR і PDF працюють через окрему allow-listed projection;
  послідовний report ID не є public key.
- Profile/admin UI, server-side довідники та versioned `idc-demo-v1` реалізовані.
- Operational analytics обмежена admin: status-зріз експертів, server-timed
  active-time майбутніх draft-сесій, окремий elapsed time до першого save
  майстра та review-cycle адміністраторів. Period
  filters мають різні явні date sources; немає ML, ринкової ціни, рейтингу або
  відновленого з timestamps active-time.
- Ринкові дані мають окрему admin-only межу `/market-data/*`: provider catalog,
  future-only policy системних орієнтирів, immutable snapshot-и OpenFacet та
  frozen NBU FX. Нові valuation мають private append-only події, але safe audit
  не запускає external fetch, approval або запис даних, тому перевіряє лише
  401-межі GET-маршрутів; `market/price`
  лишається legacy demo-індексом, а не джерелом ринкової оцінки.
- Автоматизовані regression-набори існують: pytest, Node/DOM та Playwright.
  Їхні команди описано в `AGENTS.md` і `docs/local-start.md`.

## Безпечний локальний API smoke

`npm run audit:api` приймає лише `localhost`/`127.0.0.1`, не використовує
токенів і не змінює дані. Він перевіряє 15 контрактів: root/OpenAPI/CORS,
публічні mappings і паспорт-404, а також 401-межі для private reports,
detail, profile, users, experts, reference values, обох admin-only analytics
endpoint-ів і read-only market-data endpoints. Звіти створюються лише локально в ігнорованому
`docs/audits/`.

`POST /report-wizard-sessions` навмисно не входить до safe smoke: це
авторизований write endpoint, який створює короткоживучий lease. Його RBAC,
atomic claim разом із `POST /reports`, replacement вкладки й offline fallback
покривають ізольовані API та Playwright-тести.

Перед запуском має працювати локальний FastAPI на `:8000`:

```powershell
cmd /c "cd frontend && npm run audit:api"
```

## Історичний знімок аудиту 14.09.2026

## Підсумок

- На момент аудиту тимчасовий Uvicorn на `127.0.0.1:8002` пройшов ранню версію smoke на **10/10**.
- Уже відкритий процес на `127.0.0.1:8000` під час аудиту відповідав на OpenAPI, CORS і неавторизовані межі, але чотири маршрути з доступом до БД зависали; аудит дав **6/10**. Це runtime-інцидент процесу, а не підтверджений дефект коду: перезапуск backend і повторний аудит мають бути першим кроком наступної робочої сесії.
- У коді підтверджено критичний дефект створення звіту, прогалини RBAC, розбіжності API ↔ frontend і розходження фактичної БД із моделями/seed.
- На той момент автоматизованих unit, API integration і browser E2E тестів не було. Зараз це твердження неактуальне: див. «Поточний стан» вище.

## API: рішення за маршрутами на 14.09.2026

| Маршрут | Стан | Рішення | Доказ / наступна дія |
| --- | --- | --- | --- |
| `GET /` | Працює | Залишити | Технічний smoke endpoint; не замінює майбутній health-check БД. |
| `POST /token` | Працює локально, небезпечна реалізація auth | Виправити, зберегти | Bcrypt для seed, обов’язковий `SECRET_KEY`, обробка 401 у frontend; не логувати секрети. |
| `GET /users/` | Захищений admin маршрут | Залишити; додати UI пізніше | Перевірка admin є. Потрібні валідація ролей і admin-екран. |
| `POST /users/` | Захищений admin маршрут | Виправити, зберегти | Обмежити роль переліком, перевірити password-політику та bcrypt seed. |
| `PUT /users/{expert_id}` | Захищений admin маршрут | Виправити, зберегти | Потрібні валідація ролі, чіткі 404/422 і майбутній admin UI. |
| `DELETE /users/{expert_id}` | Захищений admin маршрут | Залишити з рев’ю | Є 404; потрібні тести RBAC та рішення щодо самовидалення/admin-last-user. |
| `GET /users/me` | Захищений маршрут | Залишити; додати UI | Контракт працює для межі без токена; профільної сторінки немає. |
| `GET /experts/` | Незавершений | Виправити | `read_experts()` обчислює список, але повертає `None`; авторизований виклик дасть помилку response model. Не є дублікатом `/users/`: повертає лише не-admin експертів. |
| `GET /diamonds/` | Працює | Виправити контракт; додати UI | Dashboard викликає маршрут, але `DiamondReportSchema` не повертає `shape` і `cut_grade`, які UI намагається показати. |
| `GET /diamonds/{report_id}` | Працює для 404 і читання | Залишити; додати UI | Немає `view-report.html`; перед публічним паспортом погодити, які поля можуть бути публічними. |
| `POST /diamonds/` | Підтверджено зламаний | Виправити | `crud.py` передає `evaluation_time_min`, але модель/БД мають `evaluation_time_sec`; створення впаде до запису. Форма також не має shape selector і не підтримує файли. |
| `PUT /diamonds/{report_id}` | Неповний RBAC | Виправити | Будь-який авторизований користувач може змінити будь-який звіт; відсутній 404 для неіснуючого звіту. Потрібне owner/admin правило та edit UI. |
| `DELETE /diamonds/{report_id}` | Admin-only, неповна семантика | Виправити | Неіснуючий звіт повертає успіх замість 404. |
| `GET /statistics/expert-performance` | Працює | Залишити після рішення про доступ; додати UI | Публічно повертає usernames і статистику; визначити, чи це допустимо до сторінки аналітики. |
| `GET /market/mappings` | Працює | Залишити; інтегрувати в UI | Frontend дублює mappings статичними масивами й не використовує API. |
| `GET /market/price` | Реалізований | Залишити; інтегрувати/уточнити | UI калькулятора використовує власну фіксовану базову ціну, а не endpoint. |
| `POST /market/price` | Захищений admin маршрут | Залишити; додати UI пізніше | Є server-side admin перевірка; потрібні валідація та admin-екран. |

**Висновок щодо дублікатів.** Повних дубльованих HTTP endpoint-ів не знайдено. `/users/` і `/experts/` мають різне призначення. Натомість є дублювання логіки: невикористаний `crud.get_diamonds()` поруч із `get_reports()`, дубльований API origin у двох frontend-файлах, статичні mappings і окрема frontend-формула ціни.

## Актуалізація 2026-09-14: report-api-correctness

- `GET /experts/` тепер повертає список не-admin експертів.
- `DiamondReportSchema` містить `shape` і `cut_grade`, які використовує dashboard.
- Створення звіту записує `evaluation_time_sec`; значення 5–40 хвилин явно конвертується у секунди.
- `PUT /diamonds/{report_id}` дозволений лише власнику або admin і повертає 404 для відсутнього звіту; `DELETE` для admin також повертає 404.
- Невикористаний `crud.get_diamonds()` вилучено, бо `get_reports()` є єдиним шляхом списку з фільтрацією та сортуванням.

## Frontend ↔ API

| Функція / сторінка | Фактичний стан | Рішення |
| --- | --- | --- |
| Login | `login.html` викликає `/token`; CORS та неавторизовані межі перевірені | Залишити, але централізувати API-клієнт і посилити auth. |
| Dashboard | `dashboard.html` викликає `GET /diamonds/`, фільтри й пошук передаються | Виправити response model, прибрати mock rows як джерело даних, додати detail/edit flows. |
| Create report | Є wizard і `POST /diamonds/` | Виправити backend defect, shape, серверну валідацію, файли/дата або прибрати не підтримувані поля. |
| Public search / passport | Landing лише редіректить на відсутній `view-report.html` | Створити detail/passport сторінку після рішення щодо публічних даних. |
| Profile / analytics links | Посилання ведуть на відсутні `profile.html` і `ml-analysis.html` | Не показувати як готові; реалізувати окремими вертикальними зрізами. |
| Mappings і market price | Є endpoints, але UI використовує hardcode | Перевести форму/калькулятор на серверні довідники або чітко визначити локальну preview-логіку. |

## Auth, RBAC і безпека

| Пріоритет | Спостереження | Дія |
| --- | --- | --- |
| Високо | Seed зберігає тестові паролі у відкритому вигляді, а `verify_password()` порівнює їх напряму. | Хешувати seed bcrypt і прибрати пряме порівняння. |
| Високо | `SECRET_KEY` має fallback у коді. | Зробити змінну обов’язковою, додати безпечний `.env.example`. |
| Високо | `PUT /diamonds/{report_id}` не перевіряє власника або admin. | Ввести server-side policy owner/admin і API-тести. |
| Середньо | Pydantic-схеми не обмежують діапазони grades, чисел чи дозволених ролей. | Додати `Field`/enum-обмеження після узгодження доменних правил. |
| Середньо | Header вставляє username з `localStorage` через `innerHTML`. | Рендерити текст через `textContent`/DOM API й не вважати localStorage довіреним. |
| Інформаційно | CORS regex обмежено localhost/127.0.0.1 і підходить для локального BrowserSync. | Для production замінити точними HTTPS origins. |

## Дані, схема й seed

- Read-only інспекція підтвердила: `diamond_oltp` має `experts` і `diamond_reports`; `diamond_market` — `grade_mappings` і `market_price_reference`.
- У фактичній `diamond_analytics` є таблиця `ml_results` із сімома полями, але в `backend/models.py` немає моделі, а `scripts/seed_db.py` не створює, не очищує й не наповнює її. Це schema drift: таблицю слід або формально включити в майбутній аналітичний контур з міграцією, або окремо прибрати після рішення щодо даних.
- `diamond_reports` має FK на `experts`, але фільтри `is_sold`, пошук `report_id` і сортування `report_date`/`price` не мають спеціальних індексів. Для малого seed це не блокер; перед масштабуванням потрібні вимірювання та індекси за реальними запитами.
- На момент аудиту `scripts/seed_db-start.py` був застарілим альтернативним сценарієм. У наступному `secure-local-foundation` його вилучено; актуальним лишився `scripts/seed_db.py` з bcrypt seed-паролями та відтворенням усіх трьох схем. Руйнівний запуск нового seed ще не виконувався.

## Неперевірені межі

- Авторизовані POST/PUT/DELETE не виконувалися, щоб не змінювати дані.
- Не виконувалися seed, SQL-мутації, міграції, dependency audit та browser E2E.
- Поведінку endpoint-ів на `:8000` після перезапуску треба повторити через `npm run audit:api`.

## Рекомендований порядок наступних задач

1. `secure-local-foundation`: конфігурація, bcrypt seed, `SECRET_KEY`, cleanup legacy seed.
2. `report-api-correctness`: `/experts/`, створення/оновлення/видалення звітів, response contracts, RBAC.
3. `testing-foundation`: pytest і ізольований test DB, спочатку IDC/ML/auth/RBAC/API.
4. `reports-ui-integration`: dashboard, створення, detail/passport та редагування як послідовні вертикальні зрізи.
