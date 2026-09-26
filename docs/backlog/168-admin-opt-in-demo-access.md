# 168 — Opt-in доступ адміністратора до «Демо»

## Мета

Зробити synthetic demo-контур свідомо увімкнюваним для конкретного
адміністратора. За замовчуванням він вимкнений: «Демо» не видно в меню, а
direct URL та demo API не розкривають існування ресурсу. Це не змінює
`synthetic-demo-v4`, operational `DR-*` або права експертів.

## Scope

- Додати server-side, persisted preference `demo_access_enabled` до профілю
  адміністратора з безпечним default `false`; потрібна окрема Alembic-міграція.
- Дозволити адміністратору змінювати лише власний preference у «Профілі» через
  явний checkbox і коротке пояснення: це ізольовані synthetic дані, а не
  реальні звіти чи ринкова аналітика.
- Повернути preference у безпечному current-user/profile contract, щоб header
  показував пункт «Демо» лише після підтвердженого server-side стану.
- Захистити **всі** `/demo/...` endpoints одним server-side gate: expert,
  anonymous user і admin з вимкненим preference отримують однаковий opaque
  `404`, включно з direct detail/PDF/workflow analytics URLs.
- Після успішного save змінювати меню в поточній сесії без вимоги перелогіну;
  toggle off одразу прибирає пункт меню і закриває наступні demo-запити.
- Усунути flash/flicker header: до завершення `getCurrentUser` не
  відмальовувати ні anonymous, ні admin navigation як остаточний стан.
  Ініціалізація має мати нейтральний короткий loading state, доступний для
  screen reader, без стрибка layout.
- Existing `admin` role не означає auto-opt-in. Адміністратор вмикає доступ
  тільки собі; керування opt-in інших адміністраторів не входить у цю задачу.

## Поза scope

- Зміна manifest, demo dataset, actor/workflow/SOM/provider analytics або
  public passport.
- Нові ролі, permission management UI чи аудит кадрових дій.
- Client-side-only приховування: `localStorage` не є джерелом доступу.

## Залежності

- 156, 158, 164: ізольований admin-only demo API, private preview та current
  synthetic workflow уже існують.
- Виконується перед 159 і 165, щоб нові demo tabs одразу мали єдиний gate.

## Перевірки готовності

- Міграція додає поле без зміни існуючих operational даних; всі наявні admins
  після міграції мають `demo_access_enabled = false`.
- API/integration: admin з `false`, expert і anonymous отримують opaque `404`
  для manifest, reports, detail, preview PDF та workflow analytics; admin з
  `true` має існуючий read-only доступ.
- Profile API не дозволяє змінити username, role або preference іншого
  користувача.
- Frontend unit/DOM test: header не показує anonymous menu перед resolved auth,
  показує «Демо» лише для opted-in admin і оновлюється після toggle без reload.
- `pytest`, `npm test`, `npm run build` та ручний сценарій enable → direct
  demo URL → disable → existing direct URL 404.
