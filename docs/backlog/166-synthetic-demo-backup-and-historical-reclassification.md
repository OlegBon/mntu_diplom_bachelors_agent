# 166 — Backup і контрольована класифікація історичних synthetic `DR-*`

## Мета

Безпечно підготувати можливе відокремлення від operational scope раніше згенерованих
`DR-00001…DR-01000`. Це **не** задача на видалення даних і не автоматичний backfill:
вона спершу дає відтворювану резервну копію, доказовий dry-run та перевірене
відновлення.

## Передумова

`DEMO-00001…DEMO-01000` у `synthetic-demo-v1` уже ізольовані контрактом 156–158.
Старі `DR-*` могли кілька разів генеруватися під час локальної розробки й формально
залишилися operational records. Їх не можна визначати за самим префіксом, датою,
ціною чи авторами: дозволяється лише наперед затверджений точний allow-list після
інвентаризації.

## Scope

- Додати runbook для logical MariaDB backup обох Diamant ID баз, з timestamp,
  версією Alembic, SHA-256 і переліком таблиць/кількостей. Архів зберігається поза
  Git і поза директорією робочого дерева.
- Перевіряти backup відновленням у порожню одноразову локальну БД або disposable
  MariaDB runtime; звіряти schema revision, table inventory, report/stone/event/
  market-reference counts та checksum маніфесту. Backup без restore-verification
  не є готовим до застосування.
- Створити read-only dry-run, який друкує точний список кандидатів, їхні залежності
  (stone, events, valuations, media, public passport) і відмовляється працювати,
  якщо в allow-list є пропуск або поза ним є несподіваний synthetic кандидат.
- Окремо описати рішення для схваленого списку: створити окремий immutable manifest
  на кшталт `synthetic-legacy-v1`; у транзакції змінювати тільки `reports.record_scope`
  та `reports.demo_dataset_id`. Не змінювати ID звіту, камінь, timestamps, оцінки,
  події, ціну, медіа або користувачів.
- Перед apply вимагати явного підтвердження оператора після backup + restore +
  dry-run. Після apply повторити inventory та переконатися, що operational API,
  dashboard, public passport і аналітика не бачать ці records.
- Мати вузький rollback тільки для двох полів scope/dataset, доступний доти, доки
  не з'явилися нові залежності; rollback також потребує нового backup і dry-run.

## Явні межі

- Не запускати `seed_db.py`, не чистити `DR-*`, не перейменовувати їх у `DEMO-*`
  і не змінювати локальну БД у межах планування.
- Не змішувати legacy synthetic records з `synthetic-demo-v1` без окремого manifest
  та provenance; вони можуть мати інший генератор, поля й розподіли.
- Це не замінює production backup/disaster-recovery політику з задачі deployment.

## Перевірки готового рішення

1. Backup відновлюється у disposable БД і проходить inventory parity.
2. Dry-run відтворюваний та не виконує жодного DML.
3. Apply торкається лише схвалених report IDs і лише двох полів scope/dataset.
4. Rollback повертає саме попередні значення та не зачіпає жодного іншого запису.
5. API/RBAC regression підтверджує: expert/anonymous не бачать legacy demo;
   admin бачить їх тільки у виділеному demo-наборі.

## Залежності та пріоритет

Залежить від 156, 157 і завершеної 158. Це P2 safety/data-hygiene задача: не блокує
164, 159 або 165, доки historical `DR-*` не використовуються як operational факт.
Перед будь-яким реальним apply потрібне окреме підтвердження користувача.
