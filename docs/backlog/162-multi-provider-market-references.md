# 162 — Кілька provider-ів ринкових орієнтирів

## Мета

Дати policy змогу автоматично створювати кілька незалежних, прозорих
market-reference valuations одного каменю без змішування методологій,
автоматичного усереднення або публічного перевидання provider data.

## Залежності

156 для demo scope; 141 потрібна перед додаванням IDEX як реального provider-а.
Рішення та точний migration contract — ADR-007.

## Scope

- Normalise singleton policy у enabled provider set плюс nullable dashboard
  primary provider; migration зберігає OpenFacet як enabled/primary і не
  переписує історичні valuations/events.
- Для кожного enabled provider-а independently compute/freeze valuation за
  snapshot-ом, coverage і canonical inputs. Не додавати average, total,
  hidden fallback або cross-provider ranking.
- Зробити manual confirmation provider-specific; provider, snapshot, currency,
  unit, timestamp, applicability і FX provenance залишаються immutable.
- Переробити Market Data UI: checkbox per provider, один primary selector,
  scope/terms/coverage disclosure та local optional brand asset.
- Переробити wizard, private detail і dashboard: provider cards; compact
  primary value + source + `+N` у «Орієнтир (USD)» та accessible popover.
- Provider logos — лише local vetted assets і documented usage permission;
  IDEX branding не додавати до їхнього approval. Public passport/PDF лишити
  без money/provider branding у межах цієї задачі.
- Demo generator integration: fictional `Demo Market A/B` provider metadata,
  local logos і synthetic snapshots доступні лише demo scope.

## Перевірки

- Migration upgrade/check/controlled rollback, legacy OpenFacet policy і
  valuations unchanged.
- API: enabled/primary validation, unsupported provider, two valuations,
  no aggregation/fallback, immutable provenance, RBAC і public exclusion.
- UI/E2E: desktop/mobile provider cards, primary unavailable with secondary
  available, popover `+N`, wizard preview/freeze on save, no remote logo fetch.

## Поза межами

IDEX live access, public display/licensing, provider accuracy ranking,
ML training/labels і provider operations analytics (163).
