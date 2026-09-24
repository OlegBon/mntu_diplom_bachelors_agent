# ADR-005: стратегія stone analytics і verified ML

**Статус:** погоджено для планування  
**Дата:** 2026-09-24  
**Пов'язані задачі:** 108, 120, 150, 151, 152, 153, 154

## Контекст

Diamant ID вже має admin-only operational analytics: кількість звітів за
статусом, review-cycle, server-timed active sessions і час до першого
збереження. Це корисний огляд workflow, але не рейтинг експертів, прогноз
ціни або ML.

Початковий задум описував `MLService.predict_price()`, SOM/карти Кохонена та
`is_investment_grade`. У поточному продукті є OpenFacet runtime reference і
може з'явитися IDEX Online, але немає погодженого training dataset, target,
ліцензії на derivative use, validation або model artifact. Експерт також
заповнює приватні текстові поля, для яких ідея «тональності» не визначає
практичної користі чи truthfulness.

## Рішення

### 1. Відокремити чотири контури

| Контур | Роль | Що ним не є |
| --- | --- | --- |
| Operational analytics | Приватний admin-огляд workflow та часу | Рейтинг або оцінка експерта, ML. |
| Supervised market-reference model | Відтворюваний private model reference з похибкою | Appraisal, offer, guaranteed sale price, expert conclusion. |
| SOM / ринкові сегменти | Descriptive unsupervised карта популяції | `predict_price()` або інвестиційний verdict. |
| Якість експертних текстів | Explainable підказки про повноту/структуру | Sentiment score, визначення правдивості чи рейтинг автора. |

### 2. Дані й ціна

Перший supervised експеримент може використовувати лише зафіксований
ліцензований dataset. Для кожного джерела потрібні owner, право на training і
derivative outputs, period, unit/currency, attribution, retention і data
quality report.

Ціль (target) має бути однією з явно названих величин: normalised USD/ct
market reference, actual sale price або listing/asking price. Вони не є
взаємозамінними. Natural та lab-grown популяції не змішуються за замовчуванням.

OpenFacet і потенційний IDEX використовуються тільки як runtime market
reference providers. Їхні відповіді не потрапляють у training/labels/SOM,
доки право на таке використання не погоджене письмово.

### 2a. Три рівні даних для експериментів

| Рівень | Допустиме використання | Заборона / межа |
| --- | --- | --- |
| `data/diamonds_dataset.csv`, `DR-00001`–`DR-01000` | Технічний seed experiment: import, cleaning, reproducible SOM pipeline, карта, empty/error UI. | Набір синтетичний; не є підтвердженим ринковим/training джерелом і не підтримує verified price, investment або market claims. |
| Локальні звіти після `DR-01000` | Лише після окремо задокументованої підстави, owner/consent, purpose limitation, retention і privacy review; за потреби — de-identification. | Не стають ML/SOM data за замовчуванням лише через те, що потрапили в OLTP. Не змішуються із seed без manifest і чіткого маркування. |
| Ліцензований зовнішній dataset | Лише відповідно до письмових training/derivative-use прав і dataset card. | Provider runtime responses не прирівнюються до такого dataset. |

Отже, seed може дати цінний демонстраційний SOM-механізм уже локально, але
його екран має прямо називатися synthetic development demo та не показувати
прогноз, confidence, market segment або investment quality як властивість
реального каменю.

### 3. Верифікований результат

До private UI результат не називається ML/model reference. Потрібні locked
reproducible split, baselines, метрики за сегментами, uncertainty/calibration,
versioned code/dependencies/dataset manifest/model artifact і model card.
Збережений результат не змінює IDC grades, expert conclusion, lifecycle,
market reference або historical report. Він містить provenance, timestamp,
version, unit/currency та uncertainty.

### 4. SOM і інвестиційні формулювання

SOM реалізується як окремий відтворюваний unsupervised experiment після data
contract. UI показує population, period, features, normalisation, grid/seed,
dataset/model version і межі інтерпретації. Кластери мають нейтральні описи.
`is_investment_grade`, зелений/червоний investment verdict і подібні твердження
не вводяться без окремого бізнесового, правового та data-policy рішення.

### 5. Тексти експерта

Першою допустимою функцією є локальна explainable перевірка якості заповнення:
порожній або надто короткий текст, placeholder, повтор, аномальна довжина та
узгодженість з обраним status. Це warning, не блокування, не зміна даних і не
оцінка автора. NLP/ML можливі лише після annotated corpus, rubric, privacy/
consent policy, Ukrainian/English evaluation та human review. Приватні тексти
не надсилаються зовнішньому LLM без окремого рішення.

## Наслідки

- `ml_results` лишається порожньою reserved schema, без API і UI.
- Макет SOM з Figma — дизайн-орієнтир, не обіцянка поточної функції.
- Наступні незалежні задачі: 151 (data contract), 152 (supervised experiment),
  153 (SOM) і 154 (text quality).
- Staging/PostgreSQL не є передумовою локального data/experiment етапу, але
  реальна IDEX integration не починається до 141/161.
