# Synthetic SOM demo

## Призначення

«Демо → Камені» показує технічний, відтворюваний приклад карти Кохонена
(SOM) на ізольованому наборі `synthetic-demo-v4`. Це спосіб пояснити
механіку сегментації та інтерфейс, а не оцінка каменю, ринковий прогноз,
інвестиційний висновок чи verified ML.

Доступ мають лише адміністратори, які явно ввімкнули «Демо» у власному
профілі. Для експертів, гостей і адміністраторів без opt-in API та UI
відповідають opaque `404`.

## Як формується карта

1. Скрипт читає лише `DEMO-*` одного manifest-bound dataset.
2. До вектора входять вага, color, clarity, system Final Cut, proportions і
   дозволений synthetic reference у `USD/ct`.
3. `synthetic-provider-policy-v1` відбирає один fictional provider-derived
   reference для каменю: пріоритетний `Demo Market B`, або дозволений fallback
   `Demo Market A`. Якщо обидва значення за умовами сценарію недоступні,
   весь вектор виключається — заборонене значення не підставляється.
4. Ознаки нормалізуються; SOM 10×10 навчається з фіксованим seed. Кожному
   каменю призначається найближча клітинка.
5. Результат зберігається як immutable artifact: checksum набору, версія,
   schema features, normalisation, coverage та `report → cell` assignments.
   `GET /demo/.../som` лише читає artifact і ніколи не навчає модель у запиті.

Повторна генерація того самого набору й artifact version є idempotent. Команда
для явного створення artifact:

```powershell
.\.venv\Scripts\python.exe scripts\generate_synthetic_som_artifact.py --apply
```

## Як читати UI

- Основна карта показує схожість synthetic профілів. Число у клітинці —
  кількість включених demo-звітів.
- Якщо звіт не вибрано явно, карта відкриває найновіший eligible `DEMO-*`
  звіт як «Початковий приклад». Це server-side deterministic default; він не
  залежить від випадковості. `DEMO-00999` лишається окремим показовим звітом з
  вкладеннями, але не є прихованим default карти.
- «Зони SOM A–D» — великі 5×5 області для читабельності карти. Це не
  алгоритмічно названі класи, не grade, не technical/mass-market/investment
  категорії та не властивість окремого каменю.
- «У сусідстві» включає поточну клітинку і до восьми прилеглих клітинок.
- Профіль вибраного каменю показує його 4C, Final Cut, клітинку, peers та
  дозволений synthetic reference. Посилання peers і дія `⋮ → Аналіз SOM`
  відкривають ту саму карту з новим marker.
- «Демо-орієнтир сегмента» — діапазон synthetic references по всій зоні SOM,
  не predicted price і не фактична ринкова/продажна ціна.
- У правій колонці кожного demo-звіту кнопка «Аналіз на карті SOM» відкриває
  саме цей `DEMO-*` звіт на карті. Для реальних звітів такого переходу немає.
- «Огляд карти» показує охоплення policy scenario, зайняті клітинки,
  найщільнішу клітинку, найбільшу зону SOM та використання fictional
  `Demo Market A/B`. Це властивості карти, а не дублювання фільтрів звітів.

## Межі та майбутнє

`Demo Market A/B` — вигадані джерела. Policy scenario — тест технічного
per-feature gating, а не юридична інтерпретація умов реального provider-а.
OpenFacet, IDEX та operational reports не входять у цей artifact.

Для real SOM потрібні data contract, дозволи на конкретний спосіб
використання provider-derived features, quality/coverage report, versioned
artifact і validation. До цього real UI показує контрольований unavailable
state, а не порожню або імітаційну карту. Деталі — у
[ADR-005](../decisions/005-analytics-and-verified-ml-strategy.md) та задачах
[151](../backlog/151-analytics-data-contract-and-quality.md)–
[153](../backlog/153-stone-analytics-visualization.md).

## Карта synthetic benchmark сегментів

Під основною SOM-картою є друга проєкція тих самих координат: «Карта synthetic
benchmark сегментів». Для кожної непорожньої клітинки backend обчислює медіану
лише того дозволеного synthetic reference, який уже потрапив до immutable
artifact, поділеного на вагу каменю (`USD/ct`). Після цього медіани клітинок
розподіляються на чотири детерміновані nearest-rank квартильні смуги.

Колір показує тільки відносний рівень synthetic benchmark у цьому artifact;
це не total USD, predicted price, market value чи інвестиційна категорія.
Обраний звіт має той самий marker на обох картах. Порожні клітинки позначені
нейтрально й не входять до розрахунку квартилів. На карті значення компактні
(`3,1k`), а повний `USD/ct` доступний у доступній назві й підказці клітинки;
легенда розміщується праворуч на desktop і переходить під карту на mobile.
