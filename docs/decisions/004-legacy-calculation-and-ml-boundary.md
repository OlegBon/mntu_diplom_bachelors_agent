# ADR-004: legacy-перерахунок оцінок і межа майбутнього ML

**Статус:** погоджено для локального MVP  
**Дата:** 2026-09-23  
**Пов'язані задачі:** 085, 105, 110, 120

## Контекст

Після переходу на `Stone → DiamondReport` чинний workflow зберігає system
grades (`system_proportions_grade`, `system_cut_grade`) разом із
`calculation_rule_version` та окремими expert-confirmed grades. Водночас у
`DiamondReport` лишилися historical compatibility-поля, зокрема legacy
геометрія, grades, `price` і `evaluation_time_sec`.

Скрипт `scripts/recalc_grades.py` читав усі `DiamondReport`, перераховував
лише legacy `proportions_grade`/`cut_grade` через старі поля та безумовно
виконував `commit`. Він не мав dry-run, обмеження report/status, автора,
правила/version, події аудиту, backup або rollback. Скрипт не був чинним
`/reports` write-flow і міг переписати historical або issued дані так, що
legacy та system-поля розходилися б за змістом.

`MLService` уже вилучено як demo-евристику. Таблиця `diamond_analytics.ml_results`
існує тільки як порожній reserved schema; готових API, model artifact або
навчених даних немає.

## Рішення

### 1. Retire legacy bulk recalculation

`scripts/recalc_grades.py` вилучається. Його не замінюють масовою командою в
межах MVP. Historical projection-колонки не очищаються, не backfill-яться та
не переобчислюються автоматично.

Чинні джерела істини:

| Дані | Джерело / межа |
| --- | --- |
| Фізичні характеристики | Нормалізований `Stone`. |
| System Proportions / Final Cut | Детермінований `DiamondCalculator`, збережений у report із versioned ruleset. |
| Expert grades | Явне рішення експерта; Final Cut серверно похідний від expert Proportions, Polish і Symmetry. |
| Legacy grades і `price` | Compatibility/historical projection, не підстава для UI, lifecycle, експертного висновку або ринкової ціни. |

Нова IDC-методика оформлюється новою версією ruleset. Вона застосовується до
нових report або наступного штатного збереження дозволеної `draft`; не
переписує `review`, `issued` чи `void`. Зміна методики не означає
ретроактивну зміну історичного документа.

### 2. Умови майбутнього read/write інструмента

Якщо з'явиться регуляторна або виправна потреба у перерахунку, це окрема
задача і окремо погоджений command. До write-режиму він обов'язково має:

1. read-only `--dry-run` за замовчуванням із машино- та людиночитаним diff;
2. explicit scope: список `report_id`/статуси/дата, заборона неявного «усі»;
3. ідентифікатор ruleset, checksum коду, actor, час запуску та append-only
   audit trail;
4. незалежну перевірку normalized `Stone`, поточних system і expert даних;
5. попередньо перевірений backup/restore і rollback plan;
6. окрему авторизацію та підтвердження перед будь-яким commit.

Такий інструмент не підмінює новий виправлений report, якщо workflow або
правила вимагатимуть саме новий документ.

### 3. Межа deterministic IDC і ML

IDC-калькулятор лишається детермінованою системною функцією поточного
ruleset. Він не є повною методикою IDC, сертифікацією, ML або експертним
судженням. ML не може змінювати system/expert grades, lifecycle, passport,
ринковий орієнтир чи commercial status.

Будь-який ML-результат, особливо пов'язаний із ціною, потребує окремого
контракту й може бути лише явно позначеним неекспертним результатом. До
реалізації потрібні:

- ліцензоване джерело та опис призначення labels; окреме трактування natural
  і lab-grown каменів;
- versioned dataset із часовим діапазоном, feature schema, правилами очищення
  й поділом train/validation/test без leakage;
- versioned training code, model artifact, залежності, random seed,
  hyperparameters і checksum;
- зафіксовані baseline, метрики та acceptance thresholds;
- immutable provenance результату: report, input feature schema, dataset/model
  version, час, обмеження застосовності й, за потреби, confidence;
- незалежний дозвіл на UI/API відображення без змішування з market reference.

Карта Кохонена (SOM) у вкладці «Камені» може бути лише дослідницькою
кластеризацією. До її показу потрібні опис population/dataset, normalization,
grid, hyperparameters, seed, model artifact і правила інтерпретації кластерів.
Вона не створює ціну, grade, ризиковий рейтинг або експертний висновок.

## Наслідки

- У локальному MVP немає bulk перерахунку historical grades.
- `ml_results` не заповнюється і не має публічного або private API.
- Документація розрізняє IDC system calculation, expert confirmation, legacy
  `price` і versioned market reference.
- Retirement legacy projection-колонок залишається окремим етапом після
  інвентаризації фактичних читань/записів та міграційного плану.
