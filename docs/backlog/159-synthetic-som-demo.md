# 159 — Synthetic SOM demo для admin

## Мета

Показати технічний механізм карти Кохонена на isolated synthetic dataset,
не видаючи його за ринкову, інвестиційну або verified ML-аналітику.

## Scope

- Приймати тільки manifest `synthetic-demo-vN` із 157, у якого server-side
  `analysis_eligibility` містить `synthetic_som`; endpoint отримує `dataset_id`,
  а не довільні report IDs. Жодних operational reports, OpenFacet/IDEX responses
  чи private texts.
- Versioned reproducible SOM experiment: feature schema, normalisation, grid,
  random seed, training code/dependencies, dataset checksum і report→cell map.
- Використати окремий versioned `synthetic policy scenario` поверх поточного
  `synthetic-demo-v4`, а не перевипускати 1 000 reports лише для policy cases.
  Scenario імітує дозволене, недозволене та прострочене використання
  fictional `Demo Market A/B` values на рівні feature provenance. Він перевіряє
  deterministic per-feature selection/exclusion, coverage summary і те, що
  заборонене значення не потрапляє до artifact. Це demonstration механізму, не
  юридичне рішення і не policy реального provider-а.
- Admin-only карта: population/count, dataset version, feature list, methods,
  timestamp, neutral cluster descriptions і явний banner
  `Synthetic development demo — не ринкова аналітика`.
- Показ selected demo report marker лише в demo mode. Не називати кластери
  technical/mass-market/investment без окремого підтвердженого контракту;
  не показувати confidence, predicted price чи `is_investment_grade`.
- Розмістити карту у вкладці «Камені» admin-only розділу «Демо» й узгодити її
  `від / до / за весь час` зріз із задачами 164 та 165. Список demo-звітів
  зберігає власні dashboard filters і не є джерелом неявного SOM slice.
- Права панель показує пояснюваний technical profile: SOM cell, population
  клітини/сусідства, 4C/geometry, найближчі synthetic peers, описовий segment
  summary і synthetic segment reference range. Велике value має бути явно
  назване synthetic reference/scenario, а не predicted price; IDC Final Cut
  показується як детермінований system result, а не прогноз якості.
- Artifact зберігається окремо від `diamond_analytics.ml_results`: metadata,
  checksum, schema/normalisation/coverage та immutable `report → cell`
  assignments належать лише `diamond_oltp.demo_som_*`. API ніколи не тренує
  модель у GET-запиті; генератор створює artifact окремою явною командою.
- Після основної карти додати другу thematic проєкцію тих самих клітинок:
  synthetic benchmark segment map за медіанним дозволеним `USD/ct`. Вона має
  спільний marker, явну легенду квантилів і не є predicted price, market
  value або investment category.

## Перевірки

Reproducible artifact на тому самому manifest/seed, stable cell mapping,
admin-only API/UI, expert/anonymous 404, rejection для dataset без
`synthetic_som` або для чужого report ID, empty-state без dataset та a11y без
покладання лише на колір. Synthetic policy scenario має довести, що один report
не дублюється через двох provider-ів, а недозволені/прострочені values відсутні
з feature vectors та artifact; UI показує coverage/exclusion summary.

## Залежності

156 і 157. Це не замінює 151–153: real-world verified analytics починається
лише після data licence, quality contract і validation.
