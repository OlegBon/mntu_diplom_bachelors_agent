# Ruleset `idc-demo-v1`: межі та оновлення

## Призначення

`idc-demo-v1` — незмінний **внутрішній технічний ідентифікатор** ruleset локального
MVP Diamant ID, а не назва або версія документа IDC. Він дає
детермінований server-side preview для Round Brilliant, але не є повною
реалізацією чи юридичним підтвердженням відповідності *IDC Rules for Grading
Polished Diamonds, 6th edition (2013)*. Слово `July` з локальної назви PDF не
входить до назви документа на його титульній сторінці.

Усі нові report отримують `calculation_rule_version=idc-demo-v1`. Історичні
рядки, у яких версії не було, після migration `0007_grading_rulesets` чесно
позначаються `legacy-unversioned-v1`; їхні grades не змінюються і не
переобчислюються.

## Матриця відповідності

| Тема IDC 2013 | У `idc-demo-v1` | Межа MVP |
| --- | --- | --- |
| Proportions round brilliant | table %, total depth %, crown angle, pavilion angle; однакові дані дають однаковий grade | Не використовує всі виміри та спостереження IDC: зокрема girdle, culet, crown/pavilion height, angle sum і візуальні ефекти. |
| Polish | Grade обирає експерт із контрольованої серверної шкали | Застосунок не може замінити огляд поверхні каменю під збільшенням. |
| Symmetry | Grade обирає експерт із контрольованої серверної шкали | Застосунок не фіксує весь набір геометричних і візуальних спостережень IDC. |
| Final Cut | Системний preview: worst component із system Proportions, Polish, Symmetry. Експертний підсумок: worst component із expert Proportions, Polish, Symmetry | Це MVP-алгоритм, не повна IDC interdependency table. |
| Nature, treatment, disclosure | Є контрольовані поля origin, treatment та identification | Набір і текст звіту не претендують на повний склад сертифіката IDC. |

Через ці межі UI повинен називати результат «спрощений системний розрахунок
Diamant ID» і наводити його методичну основу, а не показувати технічний код
`idc-demo-v1` чи називати результат «IDC-сертифікацією».

## Джерела оцінок у report

| Значення | Джерело | Чи редагує експерт |
| --- | --- | --- |
| System Proportions | Серверний `DiamondCalculator` із геометрії | Ні; це preview. |
| System Final Cut | Серверний `DiamondCalculator` із system Proportions, Polish, Symmetry | Ні; це preview. |
| Polish, Symmetry | Експертні select із server `grade_mappings` | Так. |
| Expert Proportions | Одна експертна оцінка з server `grade_mappings` | Так. |
| Expert Final Cut | Сервер із Expert Proportions, Polish, Symmetry | Ні. |

Отже, `expert_cut_grade` зберігається у report як похідне історичне значення,
а не приймається від клієнта. Для `review → issued` потрібна експертна оцінка
Proportions: після неї server гарантує наявність несуперечливого Final Cut.

## Безпечна зміна правила

Нова редакція IDC або інша методика не редагується у UI як окремі пороги.
Замість цього створюється нова окрема task/release:

1. Розібрати первинний документ та зафіксувати, які поля, алгоритм і disclosure
   змінюються.
2. Додати новий immutable `ruleset_id` із назвою, джерелом, редакцією,
   effective date, алгоритмом і scope note.
3. Реалізувати код і міграцію лише для нового ruleset, додати позитивні,
   граничні й некоректні test vectors.
4. Провести review та явно активувати ruleset для нових report.
5. Не змінювати historical report, public passport або вже переданий PDF.
   Нова експертна оцінка створюється як новий report/revision із посиланням на
   попередній, коли такий workflow буде реалізовано.

## Довідники та права admin

- **System-locked:** ролі, lifecycle, RBAC і алгоритми не редагуються в UI.
- **Ruleset-scoped:** grade scales, терміни та допустимі disclosures належать
  конкретному ruleset і можуть з'явитися лише у контрольованому release-flow.
- **Admin-local:** методи ідентифікації, місце/лабораторія видачі, шаблонні
  формулювання й переклади можуть бути окремим versioned catalog, якщо
  прив'язуються до нових report і мають reason/source/effective date.
- **Ринкові дані:** ціни, FX і provenance не є частиною цього ruleset;
  вони описані у [гайді market provider-ів](./market-data-providers.md).

Поточний admin UI для довідників — read-only. Редагований versioned catalog
не реалізований цією задачею, бо спочатку потрібен окремий контракт release,
RBAC, audit і historical snapshots.
