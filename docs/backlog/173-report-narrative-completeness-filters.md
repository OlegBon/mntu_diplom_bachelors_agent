# 173 — Фільтри повноти текстових полів звіту

## Мета

Дати admin-у робочий список private operational і isolated demo-звітів із
незаповненими текстовими даними, не показуючи тексти, не створюючи score та не
змішуючи demo з real scope.

## Контракт фільтра

У «Всі звіти» та «Демо-звіти» додати спільний multi-select
«Порожні текстові поля» з опціями:

- «Метод ідентифікації»;
- «Висновок щодо ідентифікації»;
- «Коментар експерта»;
- «Подія зміни статусу без коментаря».

Значення вважається порожнім після server-side normalisation whitespace.
Кілька вибраних опцій працюють як `OR`: звіт повертається, якщо порожнє хоча б
одне вибране поле. Активний filter відображається в URL і відновлюється після
reload разом з іншими list filters.

## Особлива семантика lifecycle-події

Остання опція не є полем `DiamondReport`. Вона означає: звіт має хоча б одну
relevant lifecycle event з порожнім `reason`.

- Для operational reports event належить `ReportEvent`.
- Для demo reports допускаються лише event-и exact `demo_dataset_id`; synthetic
  lifecycle не читає і не фільтрує operational події.
- Якщо list вже має date filter, lifecycle event перевіряється в його date
  slice. Поточні три поля звіту лишаються current values звіту, що відповідає
  фільтру списку.
- UI не називає цю опцію «Коментар до зміни статусу», щоб не створювати хибне
  враження, ніби це одне current поле звіту.

## Межі

- Лише already-authorized private list surfaces; не public passport/PDF.
- Не повертати text/reason/excerpt у list API та не будувати content-quality
  рейтинг, NLP, sentiment або performance score.
- Не створювати historical text revision. Порожній current field не є доказом
  того, що він був порожнім у минулому.
- Не поєднувати з filter за provider, SOM, оцінкою, ціною або public tracking.

## Готовність і перевірки

1. Один query contract і server-side normalisation для real/demo list routes;
   demo має exact dataset isolation і opaque access gate.
2. Frontend використовує спільний filter primitive, readable selected state і
   пояснення окремої event-семантики.
3. API tests покривають кожне поле, OR-комбінацію, date-sliced event,
   auth/RBAC та неможливість leakage між scopes.
4. Frontend build/jsdom tests перевіряють controls, URL serialisation і reset;
   responsive UI не ламає наявні list filters.
