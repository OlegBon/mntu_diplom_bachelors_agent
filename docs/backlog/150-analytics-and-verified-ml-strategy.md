# 150 — Analytics і verified ML strategy

## Мета

Відокремити вже реалізовану operational analytics від майбутньої stone
analytics/ML і визначити умови, за яких прогноз можна називати верифікованим.

## Відомий стан

Є admin-only workflow statistics; це не рейтинг експертів, не price prediction
і не ML. `ml_results` — порожня зарезервована schema.

## Етапи

1. **Data contract and quality:** ліцензований dataset, ownership, target,
   missing values, data quality, train/validation/test split і versioning.
2. **Verified experiment:** baseline, метрики, reproducible training, versioned
   model artifact, uncertainty/error, model/result provenance.
3. **Stone analytics UI:** лише після валідних результатів — розділ analytics,
   SOM/cluster visualisation, пояснення й рішення про public visibility.

## Незмінні межі

- ML результат зберігається окремо від expert conclusion, IDC grades і status.
- Він не переписує історичні reports, ціну, lifecycle або market reference.
- Немає «ML» label до dataset, validation і відтворюваного артефакту.
