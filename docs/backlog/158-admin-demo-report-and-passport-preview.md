# 158 — Admin demo report, PDF і passport preview

## Мета

Дати admin повний демонстраційний перегляд synthetic report без створення
реального публічного документа або доступу експертам.

## Scope

- Окремий admin-only demo list/detail mode та read-only actions; чіткий badge
  `DEMO · SYNTHETIC DATA` у report, вкладеннях і money provenance.
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
зміна public passport contract.
