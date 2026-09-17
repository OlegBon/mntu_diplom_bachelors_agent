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
| [121-market-data-provider-expansion-and-fx.md](./121-market-data-provider-expansion-and-fx.md) | Нові провайдери, NBU FX, freshness policy та scheduler. |
| [112-expert-active-time-and-analytics-periods.md](./112-expert-active-time-and-analytics-periods.md) | Достовірний active-time експертів і періоди operational analytics. |
| [115-profile-admin-ui-polish.md](./115-profile-admin-ui-polish.md) | Узгоджені візуальні та responsive-покращення Profile й admin UI. |
| [120-legacy-calculation-and-ml-boundary.md](./120-legacy-calculation-and-ml-boundary.md) | Безпечна доля legacy-перерахунку та межа майбутнього ML. |
| [130-public-passport-media.md](./130-public-passport-media.md) | Контрольована видимість вкладень у public passport. |
