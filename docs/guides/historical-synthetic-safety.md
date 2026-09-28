# Історичний synthetic seed: backup, доказовий dry-run і майбутній backfill

Цей guide описує безпечний контур для старих `DR-00001…DR-01000`. Він не
класифікує і не видаляє їх зараз. Поки в application немає достатнього набору
нормальних operational reports або окремо погоджених test fixtures, записи
лишаються `operational` і продовжують бути видимими у звичайному private UI.

`DEMO-…` та immutable `synthetic-demo-v4` — інший, уже ізольований контур.
Не можна змішувати два набори або вважати один доказом походження іншого.

## Чому потрібен ручний reviewed manifest

`DR-*`, дата створення, ціна, автор чи текст не є надійними ознаками
synthetic-походження. Скрипт не має евристики і не зробить припущення за цими
полями. Перед майбутнім backfill відповідальна особа переглядає інвентаризацію
та створює JSON **поза репозиторієм**:

```json
{
  "reviewed_candidate_ids": ["DR-00001", "DR-00002"],
  "approved_report_ids": ["DR-00001", "DR-00002"],
  "review_basis": "manual review of the legacy generator seed",
  "reviewed_at": "2026-09-28T12:00:00+03:00"
}
```

Два масиви мають бути однаковими. Перший фіксує повний перелік переглянутих
synthetic-кандидатів, другий — рівно ті записи, для яких можливий майбутній
write scope. Якщо є хоча б одна розбіжність, dry-run завершується помилкою.
Метадані `review_basis` і `reviewed_at` рекомендовані для audit trail, але не
вважаються автоматичним доказом provenance.

## Фаза 1 — тільки читання

Спершу запускається на поточній локальній БД старий інвентаризаційний check:

```powershell
.\.venv\Scripts\python.exe scripts\inventory_demo_seed.py
```

Потім dry-run із reviewed manifest:

```powershell
.\.venv\Scripts\python.exe scripts\historical_synthetic_reclassification.py --allow-list D:\DiamantID\private\reviewed-dr-manifest.json
```

Результат JSON містить SHA-256 нормалізованого allow-list, знайдені та відсутні
ID, поточний scope, наявність Stone і кількість прив'язаних events, valuations,
media та passports. Скрипт використовує лише `SELECT`; у нього немає
`--apply`, `--rollback`, DML чи commit path.

`ready_for_future_apply_design: true` не є дозволом на запис. Це лише означає,
що перевірені ID існують, досі operational і не мають пропущеного Stone.

## Фаза 2 — logical backup та manifest

Перед будь-яким write потрібен новий backup усіх трьох локальних Diamant ID
databases: `diamond_oltp`, `diamond_market`, `diamond_analytics`. `DB_NAME` у
local env — лише default connection; він не скасовує залежності між
schema-qualified таблицями трьох databases.

1. Створіть нову директорію **поза Git і поза робочим деревом**, наприклад
   `D:\DiamantID\backups\historical-synthetic-YYYYMMDD-HHMMSS`.
2. Зафіксуйте поточну ревізію Alembic у приватному текстовому файлі:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic -c alembic.ini current
   ```

3. Зробіть один logical dump. Додайте `-p`, якщо MariaDB запитає локальний
   пароль; його не записують у команду, Git чи manifest:

   ```bat
   D:\Path\To\MariaDB\bin\mysqldump.exe -u root --databases diamond_oltp diamond_market diamond_analytics --single-transaction --routines --events --triggers --result-file="D:\DiamantID\backups\historical-synthetic-YYYYMMDD-HHMMSS\diamant-id.sql"
   ```

4. Обчисліть SHA-256 дампу та зафіксуйте його разом із timestamp, версією
   MariaDB, Alembic revision і table/report/stone/event/market-reference
   counts у приватному `backup-manifest.json` поруч із дампом:

   ```powershell
   Get-FileHash -Algorithm SHA256 "D:\DiamantID\backups\historical-synthetic-YYYYMMDD-HHMMSS\diamant-id.sql"
   ```

Не додавайте SQL-дамп, reviewed manifest, паролі чи `backup-manifest.json` до
Git. Backup без наступної restore verification не є придатним для apply.

## Фаза 3 — disposable restore verification

Restore виконується в окремий порожній MariaDB runtime або instance на іншому
порті. Не імпортуйте дамп поверх робочого local instance.

1. Перевірте цільовий instance командою `SELECT 1`, його версію та порт.
2. Імпортуйте дамп лише у disposable instance:

   ```bat
   D:\Path\To\Disposable-MariaDB\bin\mysql.exe -u root --port=3307 < "D:\DiamantID\backups\historical-synthetic-YYYYMMDD-HHMMSS\diamant-id.sql"
   ```

3. Зіставте з `backup-manifest.json`: Alembic revision, inventory таблиць,
   count reports, stones, report events, market references і SHA-256 дампу.
   Повторіть два read-only scripts із connection, що вказує саме на disposable
   instance, або виконайте еквівалентні `SELECT COUNT(*)`.
4. Запишіть час, цільовий порт і результат parity у приватний manifest.

Якщо хоча б один показник не збігається, backup не вважається verified;
backfill не проектують і не запускають.

## Майбутній вузький write contract

Окрема задача може з'явитися лише після нового backup, успішного restore,
read-only dry-run та явного погодження оператора. Вона створює окремий
immutable dataset manifest, наприклад `synthetic-legacy-v1`, і в одній
транзакції змінює **лише**:

```text
diamond_reports.record_scope: operational -> demo
diamond_reports.demo_dataset_id: NULL -> <new immutable manifest id>
```

Вона не змінює report ID, Stone, timestamps, lifecycle, grades, valuation,
events, media, passports, accounts чи provider data. Після apply повторюють
inventory і перевіряють, що operational API, dashboard, public flows та
operational analytics не бачать ці записи.

Rollback — окрема підтверджена операція після нового backup/dry-run. Він може
повернути тільки ті самі два поля лише точному списку ID і лише доки не
з'явилися нові залежності від legacy dataset. Alembic downgrade не є rollback
даних.

