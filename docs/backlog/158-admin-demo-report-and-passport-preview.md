# 158 — Admin demo report, PDF і passport preview

## Мета

Дати admin повний демонстраційний перегляд synthetic report без створення
реального публічного документа або доступу експертам.

## Scope

- Окремий admin-only розділ «Демо» з вкладками. У цій задачі повністю
  реалізується лише «Демо-звіти»; вкладки майбутніх зрізів не показують
  вигаданих чисел і ведуть на чесний стан «заплановано».
- «Демо-звіти» повторює dashboard звичайних звітів: пошук, ті самі базові й
  розгорнуті фільтри, пагінація, badges, дворядковий money provenance та меню
  дій. Усі дії, крім перегляду й private PDF preview, read-only.
- Detail використовує той самий information architecture і visual primitives,
  що private report detail, але чітко позначений `DEMO · SYNTHETIC DATA` і не
  пропонує редагування, lifecycle transition або публікацію.
- Єдиний зріз дат для майбутніх demo-аналітичних вкладок визначатиметься їх
  окремими задачами; він не змішується з фільтрами списку demo-звітів.
- Private passport preview використовує спільну allow-listed projection і
  PDF renderer, але не створює `public_passports`, public ID, QR, anonymous
  endpoint або cacheable media URL.
- PDF preview додає `DEMO · INTERNAL PREVIEW` watermark на кожну сторінку й
  безпечні demo assets; його Content-Disposition не імітує issued client PDF.
- В окремому demo mode dashboard display використовує `DEMO · synthetic-demo-vN`;
  operational dashboard не відображає demo money.

## Перевірки

Admin може побачити preview/PDF; gemologist і anonymous отримують `404`; після
preview у `public_passports` немає нового row; PDF містить watermark; generated
public URL/QR не існують.

## Поза межами

Публічне поширення demo, QR sharing, використання реальних report/media або
зміна public passport contract; synthetic experts/admins, stone/SOM та
provider analytics (задачі 164, 159 і 165).
