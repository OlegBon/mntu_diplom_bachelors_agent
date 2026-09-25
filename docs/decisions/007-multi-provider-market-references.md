# ADR-007: кілька незалежних ринкових provider-ів

**Статус:** погоджено для планування
**Дата:** 2026-09-25
**Пов'язані задачі:** 110, 121, 122, 141, 155, 156–159, 162, 163

## Контекст

Поточна singleton `market_reference_policies` обирає один provider для
майбутнього системного орієнтиру. Це добре для OpenFacet MVP, але не дозволяє
зберегти кілька незалежних оцінок одного каменю — наприклад OpenFacet, IDEX
Online та safe synthetic provider у demo dataset — без підміни їхнього сенсу.

## Рішення

### 1. Policy керує набором provider-ів, але не створює спільну «ціну»

Майбутня singleton policy містить набір enabled provider-ів і рівно один
nullable `dashboard_primary_provider_code`. Нормалізована дочірня таблиця
policy/provider зберігає enabled state, display order та audit metadata.
Primary provider має входити до enabled набору; `NULL` означає, що dashboard
не показує одну суму за замовчуванням.

Поточний `market_provider_code=openfacet` мігрується як enabled і primary без
backfill/перерахунку historical valuations. НБУ лишається окремим FX provider,
а не альтернативним USD market-reference provider.

### 2. Кожен provider створює окремий immutable орієнтир

Для одного stone може існувати кілька `StoneValuation`: по одному на provider,
snapshot і canonical inputs. Вони не усереднюються, не сумуються, не ранжуються
як «правильніші» і не є fallback один для одного. Несумісний або непокритий
provider просто не створює свого valuation і пояснює причину.

Manual admin confirmation залишається provider-specific: вона може бути
пріоритетною презентацією **цього** provider-а, але не приховує інші джерела.
Збережені valuations, FX та report events не переписуються при зміні policy.

### 3. Presentation і брендинг

- На «Ринкових даних» provider cards мають checkbox «Автоматично додавати
  орієнтир» і окремий control «Основний для списку звітів».
- Dashboard показує колонку **«Орієнтир (USD)»**: суму primary provider-а,
  його текстову назву та `+N` інших наявних орієнтирів. Якщо primary не має
  покриття, інша сума не підставляється непомітно; показується відсутність і
  count доступних джерел. Popover розкриває всі provider-specific values.
- Wizard і private report показують окремі provider cards. Preview завжди
  пояснює, що значення фіксується тільки при save draft.
- У public passport і клієнтському PDF provider values/logos не з'являються
  за замовчуванням. Це потребує окремого disclosure/licensing рішення для
  кожного provider-а.
- Provider logo — лише локальний, перевірений asset з `brand_asset_key`; він
  доповнює текстову назву, не є remote URL і не створює implied endorsement.
  IDEX logo додається тільки після письмової brand approval. Demo providers
  використовують власні fictional local logos і існують лише у demo scope.

### 4. Provider analytics

Admin tab «Провайдери» показує freshness, schedule/operation outcome,
candidate approval, coverage нових/змінених draft, непокриті характеристики й
кількість provider-specific valuations. Він не стверджує accuracy, не формує
середній ринковий курс і не створює investment ranking.

## Наслідки

- Потрібна міграція, API/CRUD/UI/E2E regressions у 162; її не застосовувати
  без окремого підтвердження.
- 157 має генерувати щонайменше два fictional provider-и, щоб перевірити
  multi-provider UI без даних або брендингу third party.
- 163 розширює operational analytics, а 151–153 залишаються окремими від
  provider analytics і verified ML.
