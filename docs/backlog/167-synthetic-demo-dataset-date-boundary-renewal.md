# 167 — Контрольоване перевипускання synthetic demo dataset з коректною межею дат

## Мета

Виправити граничну помилку `synthetic-demo-v1`: формула розподілу дат ділить
інтервал на `count`, тому `DEMO-01000` має дату 01.01.2026 замість останнього дня
заявленого трирічного періоду. Створити відтворюваний набір, у якому всі 1 000
записів лежать у включному діапазоні від 03.01.2023 до 31.12.2025.

## Чому це окрема задача

Manifest v1 immutable, а `diamond_reports.report_id` є глобальним primary key:
`synthetic-demo-v1` і `synthetic-demo-v2` з однаковим `DEMO-00999` не можуть
існувати паралельно. Це не зміна одного поля в UI, а контрольована заміна лише
synthetic dataset після backup, dry-run і явного підтвердження.

## Scope

- Виправити pure generator formula: перший і останній записи потрапляють точно
  в обидві межі інтервалу; `count=1` має окремо визначену безпечну поведінку.
- Змінити manifest/generator version на `synthetic-demo-v2`, не переписуючи v1
  in place і не змінюючи operational `DR-*`.
- Додати read-only preview, який показує checksum, першу/останню дату, exact
  count, `DEMO-00999` та перелік очікуваних залежностей.
- До apply виконати logical backup і restore verification для локальних БД;
  використати принципи 166, але не змішувати v1 renewal з класифікацією legacy
  `DR-*`.
- Після окремого підтвердження виконати одну транзакційну операцію: видалити
  тільки v1-owned demo events/valuations/reports/stones/manifest, створити v2
  з тими самими `DEMO-00001…DEMO-01000` IDs та оновити default dataset у UI/API.
- Перевірити, що `DEMO-00999` після renewal зберігає showcase behavior, private
  PDF, no-public-passport contract і правильну дату; оновити docs/checksum.

## Межі та гарантії

- Не чіпати `DR-*`, реальні користувацькі звіти, public passports, real media,
  market snapshots або accounts.
- У v1 немає public ID/URL/QR чи real `media_assets`; збережені користувачем
  demo PDF залишаються старими локальними файлами, а нові PDF відображають v2.
- Не застосовувати migration, reset або DML без окремого підтвердження користувача.

## Перевірки

1. Generator unit test: 1 000-й запис має 31.12.2025, дати монотонні й
   детерміновані.
2. Dry-run не виконує DML та описує рівно v1-owned rows, які буде замінено.
3. Backup відновлюється у disposable БД до apply.
4. Post-apply inventory: рівно один v2 manifest, 1 000 demo reports, 2 000
   synthetic events, 2 000 valuations, нуль public demo passports.
5. API/RBAC/PDF regression: admin бачить v2, expert/anonymous — opaque `404`;
   `DEMO-00999` має тристорінковий preview, інші — одну сторінку.

## Залежності та пріоритет

Залежить від 156–158. P1: виконати перед 164, 159 та 165, щоб усі demo analytics
спиралися на заявлений часовий період. 166 лишається окремою задачею для legacy
`DR-*` і не виконується автоматично разом із цією.
