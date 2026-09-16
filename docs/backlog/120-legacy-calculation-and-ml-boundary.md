# Legacy-перерахунок оцінок і межа майбутнього ML

## Мета

Визначити безпечну долю `scripts/recalc_grades.py` та historical projection
полів `diamond_reports` після retirement `/diamonds/*`, не переписуючи
демо-дані й не повертаючи неавторитетну цінову евристику у workflow звіту.

## Передумови

- Активний private API працює через normalized `Stone` і `/reports`.
- Старий скрипт напряму перераховує legacy-колонки `DiamondReport` і виконує
  commit; його не запускали в 085.
- Старий `MLService` вилучено разом із legacy API, бо він був випадковою demo
  евристикою без відтворюваної моделі, джерела й фінансового контракту.

## Scope

- Порівняти `recalc_grades.py` з чинними системними IDC-полями та
  expert-confirmed grades.
- Погодити один із варіантів: retire скрипта або замінити versioned command
  лише з explicit dry-run, scope, audit trail і backup/rollback plan.
- Зафіксувати межу між deterministic IDC calculation та майбутнім ML,
  залежним від авторитетних даних у задачі 110.

## Не входить

- Запуск скрипта, масовий backfill або очищення legacy-колонок.
- Міграція схеми чи автоматичне оновлення цін/валют.
- Реалізація ML-моделі або вибір провайдера даних.

## Критерії готовності

- Є погоджене рішення щодо скрипта та historical projection полів.
- Будь-який майбутній write-flow має явний dry-run, обмеження scope і план
  відновлення даних.
- Документація не називає demo-прогноз, legacy `price` або ML-евристику
  ринковою чи експертною ціною.
