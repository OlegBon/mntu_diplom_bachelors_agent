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
| P1 | [175-i18n-core-and-shared-shell.md](./175-i18n-core-and-shared-shell.md) | English-first i18n core, shared shell, login and landing. |
| P2 | [176-i18n-private-report-workflow.md](./176-i18n-private-report-workflow.md) | State-preserving private report workflow locales. |
| P2 | [177-i18n-admin-demo-and-analytics.md](./177-i18n-admin-demo-and-analytics.md) | Admin, synthetic demo and analytics locales. |
| P2 | [178-i18n-public-pdf-and-release-quality.md](./178-i18n-public-pdf-and-release-quality.md) | Public/PDF locales and final i18n quality gate. |
| P2 | [151-analytics-data-contract-and-quality.md](./151-analytics-data-contract-and-quality.md) | Ліцензії, dataset, target, quality і reproducible splits. |
| P2 | [152-verified-ml-experiment.md](./152-verified-ml-experiment.md) | Baseline, validation, artifact та model-result provenance. |
| P2 | [153-stone-analytics-visualization.md](./153-stone-analytics-visualization.md) | Private descriptive SOM / market segments після якісних даних. |
| P3 | [160-platform-and-stack-decision.md](./160-platform-and-stack-decision.md) | Cloud platform ADR, current stack and TypeScript/Vite criteria. |
| P3 | [137-github-actions-continuous-integration.md](./137-github-actions-continuous-integration.md) | Reproducible CI до переходу на protected `main`, без deploy. |
| P3 | [161-postgresql-migration-and-staging.md](./161-postgresql-migration-and-staging.md) | PostgreSQL, staging, deployment and scheduler integration. |
| P3 | [140-cloud-deployment-and-provider-scheduler.md](./140-cloud-deployment-and-provider-scheduler.md) | Хмарне розгортання, managed scheduler і observability ринкових provider-ів. |
