# ADR-008: повноцінні English-first та Ukrainian локалі

**Статус:** погоджено для реалізації
**Дата:** 2026-09-30
**Пов'язані задачі:** 145, 175–178

## Контекст

Diamant ID має перейти від україномовного локального MVP до повноцінних
English-first (`en`) та Ukrainian (`uk`) presentation locales. Переклад не
може змінити API, збережені domain values, access control, report/public ID,
QR/token, lifecycle або авторський текст. Поточний frontend — статичний
Gulp/Pug/SCSS та vanilla JavaScript; TypeScript і стороння i18n-бібліотека
на цьому етапі не плануються.

## Рішення

### 1. Канонічна locale та її життєвий цикл

- Дозволені лише `en` і `uk`; невідоме значення нормалізується до `en`.
- Пріоритет: валідний `?lang=` у URL → збережений user preference → `en`.
- Перемикач зберігає preference, оновлює або прибирає лише параметр `lang`
  через `history.replaceState`, залишаючи route, hash, усі інші query
  parameters, report ID та public ID незмінними. Він не викликає navigation
  або reload.
- `document.documentElement.lang`, доступні назви контролів і title
  оновлюються в межах того самого locale change.
- Модулі, що рендерять динамічні дані, підписуються на locale change і
  перемальовують лише presentation. Form controls, поточний wizard step,
  file inputs, local draft та авторські поля не скидаються і не перекладаються.

### 2. Каталоги та повнота перекладу

- Джерело рядків — versioned frontend catalogs із стабільними семантичними
  keys (наприклад, `navigation.reports`), а не текст як ключ і не дубльовані
  inline словники у page modules.
- Кожен release key зобов'язаний мати непорожні `en` та `uk` значення.
  Автоматична підстановка англійського рядка для відсутнього українського
  перекладу заборонена: catalog-parity test має впасти до merge.
- Fallback до `en` дозволений тільки для невалідної/відсутньої locale до
  першого render. Missing key є developer error: у development він явно
  сигналізується, а release test не допускає його до користувача.
- Статичні Pug labels отримують i18n key; runtime strings у JS створюються
  лише через той самий translate/format API. Жоден сторінковий модуль не
  встановлює locale самостійно.

### 3. Дані, формати та API

- Codes (`draft`, `issued`, shape/color/clarity codes), role/permission
  decisions, IDC results, provider identifiers і API JSON лишаються
  canonical domain data. Відображувані labels мапляться на frontend keys.
- Дати, числа та валюти форматуються централізовано через `Intl` з mapping
  `en` → `en-US`, `uk` → `uk-UA`; значення, precision, currency code та
  server-side calculations не змінюються.
- API не починає повертати локалізовані domain labels. Контрольовані
  користувацькі помилки мають стабільний code/contract, який frontend може
  подати через catalog; технічні деталі не показуються як текст API error.

### 4. Public passport і PDF

- Public passport може містити `lang=en|uk` без зміни public ID або QR/token.
- PDF отримує явний validated `lang` parameter з allow-list `en`, `uk` та
  default `en`. PDF і public page використовують однакові keys для спільних
  понять; вони не перекладають report data або авторські поля.

### 5. Перевірка та межі

- Для кожного i18n зрізу обов'язкові catalog-parity/unit checks, DOM test
  перемикача та browser flow, що доводить збереження URL і релевантного
  незбереженого введення.
- Machine translation, переклад уже збережених expert comments/conclusions/
  reasons, зміна ruleset, QR/token semantics, API-localization за header або
  TypeScript migration не входять до цього рішення.

## Наслідки

Локалі виходять по функціональних поверхнях, але кожна завершена поверхня має
обидві повні мови, а не змішаний інтерфейс. Це зберігає наявний стек та дає
майбутній TypeScript-етапу чіткий, framework-neutral contract без rewrite.
