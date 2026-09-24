# 156 — Контракт та ізоляція demo dataset

## Мета

Додати server-enforced admin-only `demo` scope для synthetic reports, не
дублюючи доменні таблиці й не змішуючи demo з operational workflow.

## Scope

- Реалізувати ADR-006: `record_scope`, immutable `demo_datasets` manifest,
  `DEMO-…` ID для нових synthetic records, індекси й explicit operational
  `_next_report_id()`.
- Не вводити глобальний user/environment toggle для змішування даних: demo
  доступний лише як явний admin-only route/mode і лише якщо існує manifest.
- Провести read-only inventory `DR-00001…DR-01000`, backup/rollback plan і
  лише за окремим дозволом — класифікаційний backfill підтвердженого seed.
- Застосувати scope guard до list/search/detail/events/valuations/media/work
  sessions, dashboard actions, analytics, market attachment, pagination і
  прямого `report_id` access. Expert demo access — opaque `404`.
- Заборонити regular API/wizard створювати, змінювати або переводити demo.
  Admin default — operational; demo лише через explicit isolated mode.
- Нормалізувати семантику dashboard money: type (`SYS`/`ADM`) окремо від
  source (`OpenFacet`/майбутній IDEX); прибрати legacy `d` з operational UI.
- До генерації визначити system-origin для synthetic assets/events. Ніколи не
  підставляти існуючого admin/expert у `uploaded_by_id` або автора demo-події.

## Міграція і rollback

- Нова Alembic revision; не запускати без окремого підтвердження.
- Перед backfill: counts, ID range, referential integrity, backup і dry-run
  report. Якщо dataset provenance не однозначний — нічого не оновлювати.
- Rollback класифікації має повертати лише `record_scope`/dataset link; ніколи
  не перейменовує historical report ID і не переписує lifecycle/price.

## Перевірки

- Migration/schema: constraints, indexes, upgrade/check та controlled rollback.
- API: admin vs gemologist list/search/direct ID/each write route; demo `404`
  public passport/media; next operational ID ignores `DEMO-…`; analytics and
  provider queries exclude demo by default.
- Негативні перевірки: demo не потрапляє в public ID/QR/PDF routes, cacheable
  public response, operational counters, review queue, `next-id`, page-refresh
  і background work-session/wizard flows.
- Frontend/E2E: no demo navigation/results for expert; explicit admin mode;
  pagination/search не змішують population; `SYS`/`ADM`/source labels.

## Поза межами

- Генерація records/assets (157), admin preview (158), SOM UI (159), реальні
  ML data або public demo sharing.
