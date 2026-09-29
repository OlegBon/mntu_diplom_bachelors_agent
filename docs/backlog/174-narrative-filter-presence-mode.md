# 174 — Режим заповненості текстових полів у списках звітів

## Мета

Доповнити private фільтр 173 так, щоб admin міг знаходити не лише звіти з
пропущеними, а й зі змістовно заповненими текстовими полями. Це робоча
навігація списком, а не оцінка якості тексту, NLP або рейтинг експерта.

## UX-контракт

- Блок має нейтральну назву «Текстові поля».
- Користувач обирає одне або кілька полів: method, conclusion, expert comment
  та, лише для operational, коментар події зміни статусу.
- Явний компактний перемикач «Порожні / Заповнені» замінює неочевидну
  «інверсію»; типовим лишається «Порожні».
- Кілька обраних полів означають «хоча б одне з обраних» в обраному режимі.
- Desktop/tablet action row «Застосувати / Очистити» центрується; на mobile
  кнопки займають доступну ширину відповідно до спільного form-action pattern.
- Композиція зберігає три колонки: два поля, два поля, коротке пояснення; на
  вузькому екрані колонки складаються вертикально.

## API і семантика

- Зберегти repeatable `empty_narrative` як перелік кодів полів, щоб чинні
  private URL і посилання з analytics не ламалися.
- Додати allow-listed параметр режиму, наприклад `narrative_presence=empty|filled`;
  коли його немає, поведінка лишається `empty`.
- Current `method`, `conclusion` і `expert_comment` перевіряти тим самим
  server-side `normalize_text`, що й narrative analytics: whitespace не є
  заповненим значенням.
- Для operational `status_transition_reason` режим `filled` означає хоча б
  одну append-only `status_changed` подію з непорожнім `reason` у вибраному
  date slice; `empty` зберігає поточну семантику порожнього `reason`.
- `DemoWorkflowEvent` не має comment/reason: опція лишається disabled у двох
  режимах і demo ніколи не читає operational events.
- Список не повертає raw text, excerpt, score чи нові персональні метрики.

## Межі

- Не додавати revision history, backfill, зміну самих report/event даних або
  нову аналітику.
- Не змінювати sort, pagination, існуючі RBAC/opaque demo gate або інші
  фільтри списку.

## Критерії готовності

1. Operational і opted-in demo UI мають спільний renderer та відновлюють
   поле/режим із URL.
2. API валідовує режим, дефолтно сумісний з 173, і застосовує OR лише до
   обраних полів.
3. API-тести покривають empty/filled, normalization, operational event date
   slice, demo isolation та disabled synthetic event option.
4. Frontend-тести покривають URL serialization/restore, DOM та responsive
   action layout; `npm test`, цільовий pytest, `compileall`, doc links і
   `git diff --check` проходять.
