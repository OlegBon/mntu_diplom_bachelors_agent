# 165 — Synthetic demo provider analytics

## Мета

Показати в адмінському розділі «Демо» окрему пояснювану статистику fictional
`Demo Market A/B`, щоб перевірити UX кількох джерел без використання або
переказу ліцензованих OpenFacet/IDEX даних.

## Scope

- Вкладка «Провайдери» використовує лише immutable valuations із
  `synthetic-demo-vN`, їх provenance та спільний demo date slice.
- Показувати coverage, кількість значень, періоди, нейтральне зіставлення
  значень і явний synthetic disclaimer. Не обчислювати hidden primary price,
  не робити «точність», market share, investment verdict або рекомендацію.
- Не показувати логотипи, назви, snapshots, freshness чи operation logs реальних
  провайдерів; `Demo Market A/B` не є market source.
- Read-only drill-down веде лише на demo report. UI має loading, empty і error
  states та не змішує demo дані з operational provider analytics у задачі 163.

## Перевірки

Admin-only API/UI; expert/anonymous `404`; date slice і coverage рахуються
лише по demo scope; OpenFacet/IDEX та operational provider tables не читаються
і не змінюються.

## Залежності

156, 157, завершена 158; бажано після 164, щоб усі demo-аналітичні вкладки
мали однаковий контракт date slice.
