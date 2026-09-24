# 153 — Stone analytics і SOM-візуалізація

## Мета

Додати пояснювану private admin-аналітику ринкових сегментів лише після
якісних даних з 151 та окремого відтворюваного експерименту.

## Межі

- SOM — descriptive unsupervised segmentation, а не механізм прогнозу ціни і
  не доказ інвестиційної привабливості. Візуальна карта з Figma є концептом,
  а не готовим product contract.
- Кожна карта показує population, period, dataset/model version, features,
  метод normalisation, seed, кількість об'єктів і застереження щодо меж.
- Кластер має нейтральну назву/опис, який підтверджують агреговані ознаки.
  Назва на кшталт «investment grade» можлива лише після окремої бізнесової,
  правової та data-policy валідації; зірка позначає тільки розглядуваний report.
- Доступ admin-only, без public passport/PDF, поки окремо не погоджено
  disclosure, privacy та ліцензійні умови.

## Перевірки

Reproducible fit/transform, stable mapping report-to-cell, empty/unknown
states, accessibility без reliance лише на колір і DOM/E2E сценарій.
