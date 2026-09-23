"""Controlled manual and scheduled market-provider operations.

The module never runs at FastAPI import/startup.  A hosting scheduler invokes
the CLI command explicitly; report save only reads already persisted snapshots.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from . import crud, models
from .fx import FxProviderError, fetch_nbu_usd_uah
from .market_providers import MarketProviderError, get_market_provider


RETRY_DELAYS_MINUTES = (15, 30, 60)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def freshness_status(
    *, latest_retrieved_at: datetime | None, warn_after_hours: int,
    block_after_hours: int, now: datetime,
) -> str:
    if latest_retrieved_at is None:
        return "missing"
    if latest_retrieved_at.tzinfo is None:
        latest_retrieved_at = latest_retrieved_at.replace(tzinfo=timezone.utc)
    age = now - latest_retrieved_at
    if age > timedelta(hours=block_after_hours):
        return "stale"
    if age > timedelta(hours=warn_after_hours):
        return "warning"
    return "fresh"


def schedule_is_due(
    db: Session, *, schedule: models.MarketProviderSchedule, now: datetime,
) -> tuple[bool, int]:
    """Return whether this external operation is due and its 1-based attempt."""
    if not schedule.enabled:
        return False, 0
    local_now = now.astimezone(ZoneInfo(schedule.timezone_name))
    scheduled_for = local_now.replace(
        hour=schedule.scheduled_hour, minute=schedule.scheduled_minute,
        second=0, microsecond=0,
    )
    if local_now < scheduled_for:
        return False, 0
    scheduled_start = scheduled_for.astimezone(timezone.utc)
    operations = (
        db.query(models.MarketProviderOperation)
        .filter(
            models.MarketProviderOperation.provider_code == schedule.provider_code,
            models.MarketProviderOperation.trigger_type == "scheduled",
            models.MarketProviderOperation.started_at >= scheduled_start,
        )
        .order_by(models.MarketProviderOperation.operation_id.desc())
        .all()
    )
    if not operations:
        return True, 1
    last = operations[0]
    if last.status in {"success", "no_change", "skipped"} or last.attempt_number > len(RETRY_DELAYS_MINUTES):
        return False, 0
    completed_at = last.completed_at
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)
    retry_delay = RETRY_DELAYS_MINUTES[last.attempt_number - 1]
    return now >= completed_at + timedelta(minutes=retry_delay), last.attempt_number + 1


def _latest_same_nbu_snapshot(
    db: Session, *, rate_date: object, rate: object,
) -> models.FxDataSnapshot | None:
    return (
        db.query(models.FxDataSnapshot)
        .filter(
            models.FxDataSnapshot.provider_code == "nbu",
            models.FxDataSnapshot.rate_date == rate_date,
            models.FxDataSnapshot.rate == rate,
        )
        .order_by(models.FxDataSnapshot.fx_snapshot_id.desc())
        .first()
    )


def run_provider_operation(
    db: Session,
    *,
    provider_code: str,
    trigger_type: str,
    attempt_number: int = 1,
    actor: models.Expert | None = None,
    now: datetime | None = None,
    fx_fetcher: Callable[[], object] | None = None,
    market_provider_factory: Callable[[str], object] | None = None,
) -> models.MarketProviderOperation:
    """Fetch one provider and persist an immutable outcome without report writes."""
    started_at = now or _utc_now()
    try:
        if provider_code == "nbu":
            fetched = (fx_fetcher or fetch_nbu_usd_uah)()
            existing = _latest_same_nbu_snapshot(db, rate_date=fetched.rate_date, rate=fetched.rate)
            if existing is not None:
                return crud.create_market_provider_operation(
                    db, provider_code=provider_code, trigger_type=trigger_type, status="no_change",
                    attempt_number=attempt_number, started_at=started_at, completed_at=_utc_now(),
                    fx_snapshot_id=existing.fx_snapshot_id, message="Офіційний курс уже зафіксований.", actor=actor,
                )
            snapshot = crud.create_nbu_fx_snapshot(db, fetched=fetched, actor=actor, commit=True)
            return crud.create_market_provider_operation(
                db, provider_code=provider_code, trigger_type=trigger_type, status="success",
                attempt_number=attempt_number, started_at=started_at, completed_at=_utc_now(),
                fx_snapshot_id=snapshot.fx_snapshot_id, message="Збережено новий офіційний курс USD/UAH.", actor=actor,
            )

        fetched = (market_provider_factory or get_market_provider)(provider_code).fetch_snapshot()
        checksum = crud.market_snapshot_checksum(fetched)
        existing = (
            db.query(models.MarketDataSnapshot)
            .filter(
                models.MarketDataSnapshot.provider_code == provider_code,
                models.MarketDataSnapshot.content_sha256 == checksum,
            )
            .order_by(models.MarketDataSnapshot.snapshot_id.desc())
            .first()
        )
        if existing is not None:
            return crud.create_market_provider_operation(
                db, provider_code=provider_code, trigger_type=trigger_type, status="no_change",
                attempt_number=attempt_number, started_at=started_at, completed_at=_utc_now(),
                market_snapshot_id=existing.snapshot_id, message="Ідентичний знімок уже існує.", actor=actor,
            )
        snapshot = crud.create_market_data_candidate(db, fetched=fetched, actor=actor)
        return crud.create_market_provider_operation(
            db, provider_code=provider_code, trigger_type=trigger_type, status="success",
            attempt_number=attempt_number, started_at=started_at, completed_at=_utc_now(),
            market_snapshot_id=snapshot.snapshot_id,
            message="Створено candidate; він потребує окремого рішення адміністратора.", actor=actor,
        )
    except (FxProviderError, MarketProviderError, crud.ReportDomainError) as error:
        return crud.create_market_provider_operation(
            db, provider_code=provider_code, trigger_type=trigger_type, status="failed",
            attempt_number=attempt_number, started_at=started_at, completed_at=_utc_now(),
            message=str(error), actor=actor,
        )


def run_due_provider_operations(
    db: Session, *, now: datetime | None = None,
) -> list[models.MarketProviderOperation]:
    """Run only due provider operations; safe to call repeatedly from cron."""
    current = now or _utc_now()
    results: list[models.MarketProviderOperation] = []
    for schedule in crud.get_market_provider_schedules(db):
        due, attempt = schedule_is_due(db, schedule=schedule, now=current)
        if due:
            results.append(
                run_provider_operation(
                    db, provider_code=schedule.provider_code, trigger_type="scheduled",
                    attempt_number=attempt, now=current,
                )
            )
    return results
