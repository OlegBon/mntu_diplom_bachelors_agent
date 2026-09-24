# 152 — Верифікований експеримент прогнозу ціни

## Мета

Побудувати відтворюваний supervised baseline лише після 151 і визначити,
чи має модель достатню якість для обмеженого private display.

## Scope

- Порівняти прості baselines з вибраною моделлю на locked split; оцінювати
  MAE, median absolute error, MAPE/SMAPE лише там, де вони коректні, error by
  segment і calibration/coverage інтервалів.
- Версіонувати код, dataset manifest, feature schema, random seed, model
  artifact, training timestamp, metrics і limitation card.
- Зберігати model result окремо від report, expert conclusion, IDC grades,
  market reference та lifecycle: value, currency/unit, interval/uncertainty,
  model/dataset version і provenance.
- У private UI називати результат `model reference` лише після погодженого
  quality threshold; не використовувати «appraisal», «sale price»,
  «investment grade» або confidence, який не валідовано.

## Поза межами

- Навчання на не ліцензованих OpenFacet/IDEX відповідях, historical rewrite,
  public passport/PDF і production automation.
