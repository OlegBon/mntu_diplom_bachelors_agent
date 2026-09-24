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
| [136-sqlalchemy-pydantic-deprecation-cleanup.md](./136-sqlalchemy-pydantic-deprecation-cleanup.md) | Сумісне прибирання SQLAlchemy/Pydantic deprecation warnings. |
| [140-cloud-deployment-and-provider-scheduler.md](./140-cloud-deployment-and-provider-scheduler.md) | Хмарне розгортання, managed scheduler і observability ринкових provider-ів. |
| [141-idex-online-trial-readiness-and-mockup.md](./141-idex-online-trial-readiness-and-mockup.md) | IDEX trial readiness, English mock-up, attribution і branding boundary. |
| [145-internationalization-contract.md](./145-internationalization-contract.md) | English-first/Ukraine UI, state-preserving locale contract. |
| [150-analytics-and-verified-ml-strategy.md](./150-analytics-and-verified-ml-strategy.md) | Data contract, verified ML and future stone analytics. |
| [160-platform-and-stack-decision.md](./160-platform-and-stack-decision.md) | Cloud platform ADR, current stack and TypeScript/Vite criteria. |
| [161-postgresql-migration-and-staging.md](./161-postgresql-migration-and-staging.md) | PostgreSQL, staging, deployment and scheduler integration. |
