# 159 — Synthetic SOM demo для admin

## Мета

Показати технічний механізм карти Кохонена на isolated synthetic dataset,
не видаючи його за ринкову, інвестиційну або verified ML-аналітику.

## Scope

- Приймати тільки manifest `synthetic-demo-vN` із 157; жодних operational
  reports, OpenFacet/IDEX responses чи private texts.
- Versioned reproducible SOM experiment: feature schema, normalisation, grid,
  random seed, training code/dependencies, dataset checksum і report→cell map.
- Admin-only карта: population/count, dataset version, feature list, methods,
  timestamp, neutral cluster descriptions і явний banner
  `Synthetic development demo — не ринкова аналітика`.
- Показ selected demo report marker лише в demo mode. Не називати кластери
  technical/mass-market/investment без окремого підтвердженого контракту;
  не показувати confidence, predicted price чи `is_investment_grade`.

## Перевірки

Reproducible artifact на тому самому manifest/seed, stable cell mapping,
admin-only API/UI, expert/anonymous 404, empty-state без dataset та a11y без
покладання лише на колір.

## Залежності

156 і 157. Це не замінює 151–153: real-world verified analytics починається
лише після data licence, quality contract і validation.
