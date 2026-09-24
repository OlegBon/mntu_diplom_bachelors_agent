# Backlog

Ця папка — єдиний робочий backlog майбутніх змін Diamant ID. Кожен файл
присвячено одній темі та використовує назву `<номер>-<тема>.md`; номер задає
порядок обговорення, а не обіцянку терміну реалізації.

`docs/work_plan.md` лишається короткою дорожньою картою: він показує етапи,
пріоритети, стан і залежності. Backlog містить деталізацію активних задач, але
не дублює журнал змін.

## Як працювати з backlog

1. Перед початком суттєвої фічі, рефакторингу або архітектурної зміни створіть
   чи уточніть її файл у цій папці.
2. У задачі зафіксуйте мету, межі, залежності, відкриті рішення, критерії
   готовності та потрібні перевірки. Не перетворюйте її на журнал щоденних дій.
3. У `docs/work_plan.md` додайте короткий статус і посилання на задачу, а не
   копіюйте всю специфікацію.
4. Після реалізації видаліть файл із активного backlog. Результат, обмеження
   й виконані перевірки фіксуються у `docs/progress.md`, тематичній
   документації та merge-коміті.
5. Якщо рішення має довгострокове архітектурне або продуктове значення,
   створіть окремий запис у `docs/decisions/`, а не зберігайте завершену
   backlog-копію.

## Активні задачі

| Файл | Тема |
| --- | --- |
| [137-github-actions-continuous-integration.md](./137-github-actions-continuous-integration.md) | Reproducible CI до переходу на protected `main`, без deploy. |
| [140-cloud-deployment-and-provider-scheduler.md](./140-cloud-deployment-and-provider-scheduler.md) | Хмарне розгортання, managed scheduler і observability ринкових provider-ів. |
| [141-idex-online-trial-readiness-and-mockup.md](./141-idex-online-trial-readiness-and-mockup.md) | IDEX trial readiness, English mock-up, attribution і branding boundary. |
| [146-wizard-draft-continuity.md](./146-wizard-draft-continuity.md) | Відновлення незбереженого wizard state без hidden server draft. |
| [145-internationalization-contract.md](./145-internationalization-contract.md) | English-first/Ukraine UI, state-preserving locale contract. |
| [151-analytics-data-contract-and-quality.md](./151-analytics-data-contract-and-quality.md) | Ліцензії, dataset, target, quality і reproducible splits. |
| [152-verified-ml-experiment.md](./152-verified-ml-experiment.md) | Baseline, validation, artifact та model-result provenance. |
| [153-stone-analytics-visualization.md](./153-stone-analytics-visualization.md) | Private descriptive SOM / market segments після якісних даних. |
| [154-expert-narrative-quality-analysis.md](./154-expert-narrative-quality-analysis.md) | Explainable quality checks експертних текстів; NLP лише після policy. |
| [155-operational-and-data-quality-analytics.md](./155-operational-and-data-quality-analytics.md) | Workflow, data-quality і provider analytics без rating або public tracking. |
| [160-platform-and-stack-decision.md](./160-platform-and-stack-decision.md) | Cloud platform ADR, current stack and TypeScript/Vite criteria. |
| [161-postgresql-migration-and-staging.md](./161-postgresql-migration-and-staging.md) | PostgreSQL, staging, deployment and scheduler integration. |
