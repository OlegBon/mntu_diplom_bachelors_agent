# Backlog

Ця папка — єдиний робочий backlog майбутніх змін Diamant ID. Кожен файл
присвячено одній темі та використовує назву `<номер>-<тема>.md`; номер задає
порядок обговорення, а не обіцянку терміну реалізації.

`docs/work_plan.md` лишається короткою дорожньою картою: він показує етапи,
порядок і залежності. Backlog містить деталізацію активних задач, але не
дублює журнал змін.

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

## Пріоритети

Пріоритет — це рекомендована черга цінності та залежностей, а не обіцянка
терміну. Менший номер важливіший; точний порядок усередині одного рівня
визначають залежності у файлі задачі.

| Рівень | Значення |
| --- | --- |
| `P0` | Захищає поточний workflow або дані; виконується наступним. |
| `P1` | Наступний продуктово важливий зріз після P0. |
| `P2` | Аналітика, partner readiness або розширення після фундаменту. |
| `P3` | Staging/deployment gate після локальної перевірки. |

## Активні задачі

| Пріоритет | Файл | Тема |
| --- | --- | --- |
| P1 | [164-synthetic-demo-actors-and-workflow-analytics.md](./164-synthetic-demo-actors-and-workflow-analytics.md) | Isolated synthetic experts/admins і workflow analytics. |
| P1 | [159-synthetic-som-demo.md](./159-synthetic-som-demo.md) | Isolated reproducible SOM technical demo у вкладці «Камені». |
| P1 | [165-synthetic-demo-provider-analytics.md](./165-synthetic-demo-provider-analytics.md) | Fictional demo-provider analytics без real market data. |
| P2 | [166-synthetic-demo-backup-and-historical-reclassification.md](./166-synthetic-demo-backup-and-historical-reclassification.md) | Backup, restore verification і контрольована класифікація historical synthetic `DR-*`. |
| P2 | [141-idex-online-trial-readiness-and-mockup.md](./141-idex-online-trial-readiness-and-mockup.md) | IDEX trial readiness, English mock-up, attribution і branding boundary. |
| P2 | [145-internationalization-contract.md](./145-internationalization-contract.md) | English-first/Ukraine UI, state-preserving locale contract. |
| P2 | [163-provider-operations-and-coverage-analytics.md](./163-provider-operations-and-coverage-analytics.md) | Admin tab operations, freshness і coverage provider-ів. |
| P2 | [154-expert-narrative-quality-analysis.md](./154-expert-narrative-quality-analysis.md) | Explainable quality checks експертних текстів; NLP лише після policy. |
| P2 | [155-operational-and-data-quality-analytics.md](./155-operational-and-data-quality-analytics.md) | Workflow і data-quality analytics без rating або public tracking. |
| P2 | [151-analytics-data-contract-and-quality.md](./151-analytics-data-contract-and-quality.md) | Ліцензії, dataset, target, quality і reproducible splits. |
| P2 | [152-verified-ml-experiment.md](./152-verified-ml-experiment.md) | Baseline, validation, artifact та model-result provenance. |
| P2 | [153-stone-analytics-visualization.md](./153-stone-analytics-visualization.md) | Private descriptive SOM / market segments після якісних даних. |
| P3 | [160-platform-and-stack-decision.md](./160-platform-and-stack-decision.md) | Cloud platform ADR, current stack and TypeScript/Vite criteria. |
| P3 | [137-github-actions-continuous-integration.md](./137-github-actions-continuous-integration.md) | Reproducible CI до переходу на protected `main`, без deploy. |
| P3 | [161-postgresql-migration-and-staging.md](./161-postgresql-migration-and-staging.md) | PostgreSQL, staging, deployment and scheduler integration. |
| P3 | [140-cloud-deployment-and-provider-scheduler.md](./140-cloud-deployment-and-provider-scheduler.md) | Хмарне розгортання, managed scheduler і observability ринкових provider-ів. |
