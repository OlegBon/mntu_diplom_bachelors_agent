"""Read-only provider analytics with an explicit, policy-bound source scope.

The service deliberately knows nothing about provider catalogues, snapshots or
operations.  A caller must supply the allowed valuation kinds and provider
names.  This lets the same aggregation mechanism serve a future authorized
operational dataset without making synthetic demo facts a fallback for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from statistics import median

from sqlalchemy.orm import Session

from . import models, schemas


@dataclass(frozen=True)
class ProviderAnalyticsScope:
    """Server-defined input boundary for one permitted analytics population."""

    record_scope: str
    dataset_id: str | None
    valuation_kinds: frozenset[str]
    provider_names: frozenset[str]
    label: str


def demo_scope(dataset_id: str) -> ProviderAnalyticsScope:
    """Return the only currently activated provider-analytics source."""
    return ProviderAnalyticsScope(
        record_scope="demo",
        dataset_id=dataset_id,
        valuation_kinds=frozenset({"synthetic_demo_reference"}),
        provider_names=frozenset({"Demo Market A", "Demo Market B"}),
        label="synthetic_demo",
    )


def read_provider_analytics(
    db: Session,
    *,
    scope: ProviderAnalyticsScope,
    date_from: date | None,
    date_to: date | None,
) -> schemas.ProviderAnalyticsResponse:
    """Aggregate immutable valuations inside exactly one supplied scope.

    `scope` is intentionally a parameter rather than a demo-only constant.
    A future real-data adapter can use the same function only after it has
    supplied an authorized provider/policy allow-list.
    """
    reports_query = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == scope.record_scope,
    )
    if scope.dataset_id is not None:
        reports_query = reports_query.filter(models.DiamondReport.demo_dataset_id == scope.dataset_id)
    start = datetime.combine(date_from, time.min) if date_from is not None else None
    end = datetime.combine(date_to + timedelta(days=1), time.min) if date_to is not None else None
    if start is not None:
        reports_query = reports_query.filter(models.DiamondReport.report_date >= start)
    if end is not None:
        reports_query = reports_query.filter(models.DiamondReport.report_date < end)
    reports = reports_query.order_by(models.DiamondReport.report_id).all()
    report_by_stone = {
        report.stone_id: report
        for report in reports
        if report.stone_id is not None
    }
    stone_ids = list(report_by_stone)
    valuations = (
        db.query(models.StoneValuation)
        .filter(
            models.StoneValuation.stone_id.in_(stone_ids),
            models.StoneValuation.valuation_kind.in_(scope.valuation_kinds),
            models.StoneValuation.source_name.in_(scope.provider_names),
        )
        .order_by(models.StoneValuation.source_name, models.StoneValuation.observed_at, models.StoneValuation.valuation_id)
        .all()
        if stone_ids
        else []
    )
    grouped: dict[str, list[models.StoneValuation]] = {name: [] for name in sorted(scope.provider_names)}
    for valuation in valuations:
        grouped[valuation.source_name].append(valuation)

    providers = []
    for provider_name, entries in grouped.items():
        amounts = [entry.amount for entry in entries]
        covered_reports = {report_by_stone[entry.stone_id].report_id for entry in entries}
        latest = max(entries, key=lambda entry: (entry.observed_at, entry.valuation_id)) if entries else None
        providers.append(schemas.ProviderAnalyticsProvider(
            provider_name=provider_name,
            reference_count=len(entries),
            covered_report_count=len(covered_reports),
            first_observed_at=min((entry.observed_at for entry in entries), default=None),
            last_observed_at=max((entry.observed_at for entry in entries), default=None),
            min_amount=min(amounts, default=None),
            median_amount=Decimal(str(median(amounts))) if amounts else None,
            max_amount=max(amounts, default=None),
            latest_report_id=report_by_stone[latest.stone_id].report_id if latest is not None else None,
        ))
    return schemas.ProviderAnalyticsResponse(
        scope=scope.label,
        dataset_id=scope.dataset_id,
        date_from=date_from,
        date_to=date_to,
        candidate_report_count=len(reports),
        reference_count=len(valuations),
        providers=providers,
    )
