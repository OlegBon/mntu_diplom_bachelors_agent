# 178 — i18n public passport, PDF і release quality

## Мета

Довести public passport/PDF locale contract до release quality та закрити
загальний i18n regression/accessibility gate.

## Передумови

- 175 — i18n core і shared shell.
- 176 та 177 — усі private/admin presentation surfaces.

## Scope

- Public passport і documentation/privacy pages отримують повні `en`/`uk`
  catalogs без зміни public ID, QR або token semantics.
- PDF приймає лише validated `lang=en|uk`, default `en`; shared labels
  збігаються з public page, report data та author text не перекладаються.
- API/browser/PDF tests перевіряють allow-list, unknown locale fallback,
  locale URL preservation, catalog parity, accessibility labels і відсутність
  mixed locale на release surfaces.

## Поза межами

- Translation service, historical data rewrite, API content negotiation і
  TypeScript/Vite migration.

## Критерії готовності

- Public URL з `lang` і без нього не змінює public identity; QR веде на той
  самий паспорт.
- PDF для обох locale проходить існуючі security/media guarantees та не
  дозволяє довільний locale value.
- Повна i18n regression suite проходить у CI.
