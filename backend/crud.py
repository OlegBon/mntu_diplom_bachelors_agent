from sqlalchemy import and_, asc, case, desc, func, select
from sqlalchemy.orm import Session, joinedload
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import secrets
import uuid
from statistics import median

from . import models, schemas
from .market_providers import FetchedMarketSnapshot
from .fx import NbuUsdUahRate, convert_usd_to_uah
from .security import get_password_hash, verify_password

from .calculator import DiamondCalculator


CURRENT_RULESET_ID = "idc-demo-v1"
# Immutable internal identifier, not an IDC document title or edition. Existing
# reports retain it for reproducibility; user-facing text must name the source
# document and state the limited Diamant ID implementation separately.
# Kept as a compatibility alias for callers and serialized API contracts.
REPORT_RULE_VERSION = CURRENT_RULESET_ID
WORK_SESSION_MAX_INTERVAL_SECONDS = 60
WORK_SESSION_LEASE_SECONDS = 75
WIZARD_WORK_SESSION_LEASE_SECONDS = 14_400


class ReportDomainError(ValueError):
    """A controlled violation of the new report-domain contract."""


def _next_report_id(db: Session) -> str:
    """Return the next operational ID without considering demo identifiers."""
    report_ids = (
        db.query(models.DiamondReport.report_id)
        .filter(
            models.DiamondReport.record_scope == "operational",
            models.DiamondReport.report_id.like("DR-%"),
        )
        .all()
    )
    numbers = [int(report_id[3:]) for (report_id,) in report_ids if report_id[3:].isdigit()]
    return f"DR-{(max(numbers) if numbers else 0) + 1:05d}"


def get_demo_dataset(db: Session, dataset_id: str) -> models.DemoDataset | None:
    return db.get(models.DemoDataset, dataset_id)


def get_demo_dataset_response(dataset: models.DemoDataset) -> schemas.DemoDatasetResponse:
    """Deserialize the immutable, server-controlled scenario allow-list."""
    try:
        eligibility = json.loads(dataset.analysis_eligibility)
    except json.JSONDecodeError as error:
        raise ReportDomainError("Demo dataset manifest has invalid analysis eligibility") from error
    if not isinstance(eligibility, list) or not all(isinstance(item, str) for item in eligibility):
        raise ReportDomainError("Demo dataset manifest has invalid analysis eligibility")
    return schemas.DemoDatasetResponse(
        dataset_id=dataset.dataset_id,
        label=dataset.label,
        version=dataset.version,
        generator_version=dataset.generator_version,
        content_sha256=dataset.content_sha256,
        provenance=dataset.provenance,
        scope_note=dataset.scope_note,
        analysis_eligibility=eligibility,
        record_count=dataset.record_count,
        created_at=dataset.created_at,
    )


def require_demo_dataset_analysis_eligibility(
    db: Session, *, dataset_id: str, scenario: str,
) -> models.DemoDataset:
    """Authorize one explicitly declared synthetic-analysis scenario.

    Future demo analytics must call this boundary before selecting any report.
    It intentionally checks the persisted manifest rather than a report-ID
    prefix, query parameter, or frontend mode.
    """
    dataset = get_demo_dataset(db, dataset_id)
    if dataset is None or not dataset.provenance.startswith("synthetic-demo-v"):
        raise ReportDomainError("Demo dataset is not eligible for synthetic analysis")
    eligibility = get_demo_dataset_response(dataset).analysis_eligibility
    if scenario not in eligibility:
        raise ReportDomainError("Demo dataset is not eligible for this analysis scenario")
    return dataset


def _legacy_origin_code(origin: str) -> int:
    return {"natural": 0, "lab_grown": 1, "unknown": 2, "other": 3}[origin]


def _system_grades(stone: schemas.StoneDraft) -> tuple[int, int]:
    proportions = DiamondCalculator.evaluate_proportions(
        stone.table_percent,
        stone.depth_percent,
        stone.crown_angle,
        stone.pavilion_angle,
    )
    cut = DiamondCalculator.calculate_final_cut(proportions, stone.polish_grade, stone.symmetry_grade)
    return proportions, cut


def _expert_final_cut(
    expert_proportions_grade: int | None,
    stone: schemas.StoneDraft,
) -> int | None:
    """Derive the expert final cut from the three expert component grades."""
    if expert_proportions_grade is None:
        return None
    return DiamondCalculator.calculate_final_cut(
        expert_proportions_grade,
        stone.polish_grade,
        stone.symmetry_grade,
    )


def preview_report_calculation(db: Session, stone: schemas.ReportCalculationInput) -> schemas.ReportCalculationPreview:
    """Calculate the server-authoritative IDC preview without persisting data."""
    proportions = DiamondCalculator.evaluate_proportions(
        stone.table_percent,
        stone.depth_percent,
        stone.crown_angle,
        stone.pavilion_angle,
    )
    cut = DiamondCalculator.calculate_final_cut(proportions, stone.polish_grade, stone.symmetry_grade)
    candidate = None
    policy = get_market_reference_policy(db)
    if policy and policy.market_provider_code and stone.shape and stone.origin:
        preview_stone = models.Stone(
            shape=stone.shape,
            origin=stone.origin,
            carat_weight=stone.carat_weight,
            color_grade=stone.color_grade,
            clarity_grade=stone.clarity_grade,
        )
        candidate = prepare_system_market_reference_for_stone(
            db, stone=preview_stone, provider_code=policy.market_provider_code,
        )
    return schemas.ReportCalculationPreview(
        system_proportions_grade=proportions,
        system_cut_grade=cut,
        calculation_rule_version=REPORT_RULE_VERSION,
        system_market_reference_usd=candidate.amount if candidate else None,
        market_reference_provider_code=candidate.snapshot.provider_code if candidate else None,
        market_reference_snapshot_id=candidate.snapshot.snapshot_id if candidate else None,
    )


def _append_report_event(
    db: Session,
    *,
    report_id: str,
    action: str,
    actor_id: int | None,
    from_status: str | None,
    to_status: str | None,
    reason: str | None = None,
) -> models.ReportEvent:
    event = models.ReportEvent(
        report_id=report_id,
        action=action,
        actor_id=actor_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
    )
    db.add(event)
    return event


def _market_reference_event_reason(valuation: models.StoneValuation) -> str:
    """Return concise private provenance suitable for the report change history."""
    snapshot = f"знімок #{valuation.market_snapshot_id}" if valuation.market_snapshot_id else "без знімка"
    return f"{valuation.currency_code} {valuation.amount:.2f} · {valuation.source_name} · {snapshot}"


def _apply_stone_draft(stone: models.Stone, payload: schemas.StoneDraft) -> None:
    for key, value in payload.model_dump().items():
        setattr(stone, key, value)
    stone.updated_at = datetime.now(timezone.utc)


def _sync_legacy_report_fields(report: models.DiamondReport, stone: models.Stone) -> None:
    """Keep old projections usable; no financial or confirmation data is copied."""
    for key in (
        "shape", "measurements_length", "measurements_width", "measurements_depth",
        "table_percent", "depth_percent", "crown_angle", "pavilion_angle",
        "girdle_thickness", "culet_size", "carat_weight", "color_grade",
        "clarity_grade", "polish_grade", "symmetry_grade", "fluorescence_grade",
    ):
        setattr(report, key, getattr(stone, key))
    report.stone_origin = _legacy_origin_code(stone.origin)
    report.is_sold = stone.market_status == "sold"


def get_report_domain(db: Session, report_id: str) -> models.DiamondReport | None:
    return db.query(models.DiamondReport).filter(models.DiamondReport.report_id == report_id).first()


def get_demo_report_domain(
    db: Session, *, dataset_id: str, report_id: str,
) -> models.DiamondReport | None:
    return (
        db.query(models.DiamondReport)
        .options(joinedload(models.DiamondReport.stone))
        .filter(
            models.DiamondReport.report_id == report_id,
            models.DiamondReport.record_scope == "demo",
            models.DiamondReport.demo_dataset_id == dataset_id,
        )
        .first()
    )


def get_report_domain_list(
    db: Session,
    *,
    current_user: models.Expert,
    status: str | None,
    market_status: str | None,
    sold: bool | None,
    shape: str | None,
    color_grade: int | None,
    clarity_grade: int | None,
    cut_grade: int | None,
    carat_min: Decimal | None,
    carat_max: Decimal | None,
    price_min: Decimal | None,
    price_max: Decimal | None,
    date_from: date | None,
    date_to: date | None,
    expert_id: int | None,
    search: str | None,
    sort: schemas.ReportListSort,
    page: int,
    page_size: int,
) -> tuple[list[models.DiamondReport], int]:
    """Return an access-scoped dashboard page and its total row count."""
    query = (
        db.query(models.DiamondReport)
        .join(models.Stone, models.DiamondReport.stone_id == models.Stone.stone_id)
        .options(joinedload(models.DiamondReport.stone))
        .filter(models.DiamondReport.record_scope == "operational")
    )
    market_reference_amount = (
        select(models.StoneValuation.amount)
        .where(
            models.StoneValuation.stone_id == models.DiamondReport.stone_id,
            models.StoneValuation.valuation_kind.in_(("market_reference", "system_market_reference")),
        )
        .order_by(
            case((models.StoneValuation.valuation_kind == "market_reference", 0), else_=1),
            models.StoneValuation.created_at.desc(),
            models.StoneValuation.valuation_id.desc(),
        )
        .limit(1)
        .scalar_subquery()
    )
    if current_user.role != "admin":
        query = query.filter(models.DiamondReport.expert_id == current_user.expert_id)
    elif expert_id is not None:
        query = query.filter(models.DiamondReport.expert_id == expert_id)
    if status:
        query = query.filter(models.DiamondReport.status == status)
    if market_status:
        query = query.filter(models.Stone.market_status == market_status)
    if sold is True:
        query = query.filter(models.Stone.market_status == "sold")
    elif sold is False:
        query = query.filter(models.Stone.market_status != "sold")
    if shape:
        query = query.filter(models.Stone.shape == shape.strip())
    if color_grade is not None:
        query = query.filter(models.Stone.color_grade == color_grade)
    if clarity_grade is not None:
        query = query.filter(models.Stone.clarity_grade == clarity_grade)
    if cut_grade is not None:
        query = query.filter(models.DiamondReport.system_cut_grade == cut_grade)
    if carat_min is not None:
        query = query.filter(models.Stone.carat_weight >= carat_min)
    if carat_max is not None:
        query = query.filter(models.Stone.carat_weight <= carat_max)
    if price_min is not None:
        query = query.filter(market_reference_amount >= price_min)
    if price_max is not None:
        query = query.filter(market_reference_amount <= price_max)
    if date_from is not None:
        query = query.filter(models.DiamondReport.report_date >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.filter(models.DiamondReport.report_date < datetime.combine(date_to + timedelta(days=1), time.min))
    if search:
        query = query.filter(models.DiamondReport.report_id.ilike(f"%{search.strip()}%"))

    sort_columns = {
        "report_date_desc": (desc(models.DiamondReport.report_date), desc(models.DiamondReport.report_id)),
        "report_date_asc": (asc(models.DiamondReport.report_date), asc(models.DiamondReport.report_id)),
        "report_id_asc": (asc(models.DiamondReport.report_id),),
        "report_id_desc": (desc(models.DiamondReport.report_id),),
        "shape_asc": (asc(models.Stone.shape), asc(models.DiamondReport.report_id)),
        "shape_desc": (desc(models.Stone.shape), desc(models.DiamondReport.report_id)),
        "carat_desc": (desc(models.Stone.carat_weight), desc(models.DiamondReport.report_id)),
        "carat_asc": (asc(models.Stone.carat_weight), asc(models.DiamondReport.report_id)),
        "color_asc": (asc(models.Stone.color_grade), asc(models.DiamondReport.report_id)),
        "color_desc": (desc(models.Stone.color_grade), desc(models.DiamondReport.report_id)),
        "clarity_asc": (asc(models.Stone.clarity_grade), asc(models.DiamondReport.report_id)),
        "clarity_desc": (desc(models.Stone.clarity_grade), desc(models.DiamondReport.report_id)),
        "cut_asc": (asc(models.DiamondReport.system_cut_grade), asc(models.DiamondReport.report_id)),
        "cut_desc": (desc(models.DiamondReport.system_cut_grade), desc(models.DiamondReport.report_id)),
        "price_desc": (desc(market_reference_amount), desc(models.DiamondReport.report_id)),
        "price_asc": (asc(market_reference_amount), asc(models.DiamondReport.report_id)),
        "report_status_asc": (asc(models.DiamondReport.status), asc(models.DiamondReport.report_id)),
        "report_status_desc": (desc(models.DiamondReport.status), desc(models.DiamondReport.report_id)),
        "market_status_asc": (asc(models.Stone.market_status), asc(models.DiamondReport.report_id)),
        "market_status_desc": (desc(models.Stone.market_status), desc(models.DiamondReport.report_id)),
    }
    total = query.count()
    reports = (
        query.order_by(*sort_columns[sort])
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    _attach_latest_market_reference_summaries(db, reports)
    return reports, total


def get_demo_report_domain_list(
    db: Session, *, dataset_id: str, page: int, page_size: int,
) -> tuple[list[models.DiamondReport], int]:
    """Return one isolated demonstration dataset; never mix it with operations."""
    query = (
        db.query(models.DiamondReport)
        .join(models.Stone, models.DiamondReport.stone_id == models.Stone.stone_id)
        .options(joinedload(models.DiamondReport.stone))
        .filter(
            models.DiamondReport.record_scope == "demo",
            models.DiamondReport.demo_dataset_id == dataset_id,
        )
    )
    total = query.count()
    reports = (
        query.order_by(desc(models.DiamondReport.report_date), desc(models.DiamondReport.report_id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    _attach_latest_market_reference_summaries(db, reports)
    return reports, total


def _attach_latest_market_reference_summaries(
    db: Session, reports: list[models.DiamondReport],
) -> None:
    """Attach a transient API projection without changing stored reports."""
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    if not stone_ids:
        return
    valuations = (
        db.query(models.StoneValuation)
        .filter(
            models.StoneValuation.stone_id.in_(stone_ids),
            models.StoneValuation.valuation_kind.in_(("market_reference", "system_market_reference")),
        )
        .order_by(
            case((models.StoneValuation.valuation_kind == "market_reference", 0), else_=1),
            models.StoneValuation.created_at.desc(),
            models.StoneValuation.valuation_id.desc(),
        )
        .all()
    )
    by_stone: dict[int, models.StoneValuation] = {}
    for valuation in valuations:
        by_stone.setdefault(valuation.stone_id, valuation)
    for report in reports:
        valuation = by_stone.get(report.stone_id)
        if valuation is None:
            continue
        report.market_reference = schemas.MarketReferenceSummary(
            amount=valuation.amount,
            currency_code=valuation.currency_code,
            valuation_kind=valuation.valuation_kind,
            source_name=valuation.source_name,
            market_snapshot_id=valuation.market_snapshot_id,
            observed_at=valuation.observed_at,
            converted_amount=valuation.converted_amount,
            converted_currency_code=valuation.converted_currency_code,
            fx_snapshot_id=valuation.fx_snapshot_id,
            fx_rate=valuation.fx_rate,
            fx_rate_date=valuation.fx_rate_date,
        )


def create_report_domain(
    db: Session,
    *,
    payload: schemas.ReportCreate,
    author: models.Expert,
) -> models.DiamondReport:
    now = datetime.now(timezone.utc)
    stone = models.Stone(**payload.stone.model_dump(), created_at=now, updated_at=now)
    db.add(stone)
    db.flush()
    system_proportions, system_cut = _system_grades(payload.stone)
    expert_cut = _expert_final_cut(payload.expert_proportions_grade, payload.stone)
    report = models.DiamondReport(
        report_id=_next_report_id(db),
        report_date=now,
        examination_date=payload.examination_date,
        stone_id=stone.stone_id,
        status="draft",
        created_at=now,
        updated_at=now,
        expert_id=author.expert_id,
        expert_comment=payload.expert_comment,
        system_proportions_grade=system_proportions,
        system_cut_grade=system_cut,
        calculation_rule_version=CURRENT_RULESET_ID,
        expert_proportions_grade=payload.expert_proportions_grade,
        expert_cut_grade=expert_cut,
        expert_confirmed_at=now if expert_cut is not None else None,
        cut_grade=system_cut,
        proportions_grade=system_proportions,
        evaluation_time_sec=0,
        report_notes_length=len(payload.expert_comment or ""),
        report_sentiment=0,
        price=None,
        is_investment_grade=False,
        is_report_rejected=False,
        is_sold=stone.market_status == "sold",
    )
    _sync_legacy_report_fields(report, stone)
    db.add(report)
    db.flush()
    _attach_wizard_first_save_timing(
        db,
        report=report,
        author=author,
        wizard_session_id=payload.wizard_session_id,
        now=now,
    )
    _append_report_event(
        db,
        report_id=report.report_id,
        action="created",
        actor_id=author.expert_id,
        from_status=None,
        to_status="draft",
    )
    db.commit()
    db.refresh(report)
    return report


def update_report_domain(
    db: Session,
    *,
    report: models.DiamondReport,
    payload: schemas.ReportUpdate,
    actor: models.Expert,
) -> models.DiamondReport:
    if report.status != "draft":
        raise ReportDomainError("Only draft reports can be edited")
    if report.stone is None:
        raise ReportDomainError("Report has no normalized stone")
    _apply_stone_draft(report.stone, payload.stone)
    system_proportions, system_cut = _system_grades(payload.stone)
    report.expert_comment = payload.expert_comment
    report.examination_date = payload.examination_date
    report.system_proportions_grade = system_proportions
    report.system_cut_grade = system_cut
    report.calculation_rule_version = CURRENT_RULESET_ID
    report.expert_proportions_grade = payload.expert_proportions_grade
    report.expert_cut_grade = _expert_final_cut(payload.expert_proportions_grade, payload.stone)
    report.expert_confirmed_at = datetime.now(timezone.utc) if report.expert_cut_grade is not None else None
    report.updated_at = datetime.now(timezone.utc)
    report.cut_grade = system_cut
    report.proportions_grade = system_proportions
    report.report_notes_length = len(payload.expert_comment or "")
    _sync_legacy_report_fields(report, report.stone)
    _append_report_event(
        db,
        report_id=report.report_id,
        action="report_updated",
        actor_id=actor.expert_id,
        from_status=report.status,
        to_status=report.status,
        reason=None,
    )
    db.commit()
    db.refresh(report)
    return report


def transition_report_domain(
    db: Session,
    *,
    report: models.DiamondReport,
    target_status: str,
    actor: models.Expert,
    reason: str | None,
) -> models.DiamondReport:
    current_status = report.status
    is_admin = actor.role == "admin"
    is_owner = actor.expert_id == report.expert_id
    allowed = (
        (current_status == "draft" and target_status == "review" and (is_owner or is_admin))
        or (current_status == "review" and target_status in {"draft", "issued", "void"} and is_admin)
        or (current_status == "issued" and target_status == "void" and is_admin)
    )
    if not allowed:
        raise ReportDomainError("This report status transition is not allowed")
    if target_status == "issued" and report.expert_proportions_grade is None:
        raise ReportDomainError("Issued reports require an expert proportions grade")

    now = datetime.now(timezone.utc)
    if current_status == "draft" and target_status == "review":
        finish_active_work_session(db, report=report)
    report.status = target_status
    report.updated_at = now
    if target_status == "issued":
        report.issued_at = now
        report.issued_by_id = actor.expert_id
    if target_status == "void":
        _deactivate_public_passports(db, report_id=report.report_id, revoked_at=now)
    _append_report_event(
        db,
        report_id=report.report_id,
        action="status_changed",
        actor_id=actor.expert_id,
        from_status=current_status,
        to_status=target_status,
        reason=reason,
    )
    db.commit()
    db.refresh(report)
    return report


def get_report_events(db: Session, report_id: str) -> list[models.ReportEvent]:
    return db.query(models.ReportEvent).filter(models.ReportEvent.report_id == report_id).order_by(models.ReportEvent.event_id).all()


def _deactivate_public_passports(
    db: Session,
    *,
    report_id: str,
    revoked_at: datetime,
) -> int:
    """Deactivate every active token for a report without changing its content."""
    return (
        db.query(models.PublicPassport)
        .filter(
            models.PublicPassport.report_id == report_id,
            models.PublicPassport.is_active.is_(True),
        )
        .update({"is_active": False, "revoked_at": revoked_at}, synchronize_session=False)
    )


def get_active_public_passport(
    db: Session,
    report_id: str,
) -> models.PublicPassport | None:
    return (
        db.query(models.PublicPassport)
        .join(models.DiamondReport, models.PublicPassport.report_id == models.DiamondReport.report_id)
        .filter(
            models.PublicPassport.report_id == report_id,
            models.PublicPassport.is_active.is_(True),
            models.DiamondReport.record_scope == "operational",
        )
        .order_by(models.PublicPassport.passport_id.desc())
        .first()
    )


def publish_public_passport(
    db: Session,
    *,
    report: models.DiamondReport,
    actor: models.Expert,
    reissue: bool = False,
) -> models.PublicPassport:
    """Publish or replace an unpredictable token for an issued report."""
    if report.record_scope != "operational":
        raise ReportDomainError("Demo reports cannot be published")
    if report.status != "issued":
        raise ReportDomainError("Only issued reports can be published")
    existing = get_active_public_passport(db, report.report_id)
    if existing is not None and not reissue:
        return existing

    now = datetime.now(timezone.utc)
    if existing is not None:
        _deactivate_public_passports(db, report_id=report.report_id, revoked_at=now)

    public_id = secrets.token_urlsafe(24)
    while db.query(models.PublicPassport).filter(models.PublicPassport.public_id == public_id).first():
        public_id = secrets.token_urlsafe(24)
    passport = models.PublicPassport(
        report_id=report.report_id,
        public_id=public_id,
        is_active=True,
        created_by_id=actor.expert_id,
        created_at=now,
    )
    db.add(passport)
    _append_report_event(
        db,
        report_id=report.report_id,
        action="passport_reissued" if existing is not None else "passport_published",
        actor_id=actor.expert_id,
        from_status=report.status,
        to_status=report.status,
    )
    db.commit()
    db.refresh(passport)
    return passport


def revoke_public_passport(
    db: Session,
    *,
    report: models.DiamondReport,
    actor: models.Expert,
) -> bool:
    """Revoke publication without mutating the issued report itself."""
    now = datetime.now(timezone.utc)
    revoked_count = _deactivate_public_passports(db, report_id=report.report_id, revoked_at=now)
    if not revoked_count:
        return False
    _append_report_event(
        db,
        report_id=report.report_id,
        action="passport_revoked",
        actor_id=actor.expert_id,
        from_status=report.status,
        to_status=report.status,
    )
    db.commit()
    return True


def get_public_passport_view(
    db: Session,
    public_id: str,
) -> tuple[models.PublicPassport, models.DiamondReport, models.Stone] | None:
    """Read the allow-listed public projection; unavailable resources stay opaque."""
    return (
        db.query(models.PublicPassport, models.DiamondReport, models.Stone)
        .join(models.DiamondReport, models.PublicPassport.report_id == models.DiamondReport.report_id)
        .join(models.Stone, models.DiamondReport.stone_id == models.Stone.stone_id)
        .filter(
            models.PublicPassport.public_id == public_id,
            models.PublicPassport.is_active.is_(True),
            models.DiamondReport.record_scope == "operational",
            models.DiamondReport.status == "issued",
            models.DiamondReport.issued_at.is_not(None),
            models.Stone.carat_weight.is_not(None),
            models.Stone.color_grade.is_not(None),
            models.Stone.clarity_grade.is_not(None),
        )
        .first()
    )


def get_media_assets(db: Session, report_id: str) -> list[models.MediaAsset]:
    return (
        db.query(models.MediaAsset)
        .filter(models.MediaAsset.report_id == report_id)
        .order_by(models.MediaAsset.media_id)
        .all()
    )


def get_media_asset(db: Session, report_id: str, media_id: int) -> models.MediaAsset | None:
    return (
        db.query(models.MediaAsset)
        .filter(models.MediaAsset.report_id == report_id, models.MediaAsset.media_id == media_id)
        .first()
    )


PUBLIC_MEDIA_ASSET_TYPES = {"stone_photo", "plotting_diagram"}
PUBLIC_MEDIA_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_public_media_assets(db: Session, report_id: str) -> list[models.MediaAsset]:
    """Return only public-safe image metadata for an already-authorized passport."""
    return (
        db.query(models.MediaAsset)
        .filter(
            models.MediaAsset.report_id == report_id,
            models.MediaAsset.is_public.is_(True),
            models.MediaAsset.asset_type.in_(PUBLIC_MEDIA_ASSET_TYPES),
            models.MediaAsset.mime_type.in_(PUBLIC_MEDIA_MIME_TYPES),
        )
        .order_by(models.MediaAsset.media_id)
        .all()
    )


def get_public_media_asset(db: Session, report_id: str, media_id: int) -> models.MediaAsset | None:
    return (
        db.query(models.MediaAsset)
        .filter(
            models.MediaAsset.report_id == report_id,
            models.MediaAsset.media_id == media_id,
            models.MediaAsset.is_public.is_(True),
            models.MediaAsset.asset_type.in_(PUBLIC_MEDIA_ASSET_TYPES),
            models.MediaAsset.mime_type.in_(PUBLIC_MEDIA_MIME_TYPES),
        )
        .first()
    )


def get_public_projection_updated_at(
    db: Session,
    passport: models.PublicPassport,
) -> datetime:
    """Return the latest public-projection change without exposing its audit data."""
    media_event_at = (
        db.query(models.ReportEvent.created_at)
        .filter(
            models.ReportEvent.report_id == passport.report_id,
            models.ReportEvent.action.in_(("media_published", "media_unpublished")),
        )
        .order_by(models.ReportEvent.created_at.desc(), models.ReportEvent.event_id.desc())
        .limit(1)
        .scalar()
    )
    return max(value for value in (passport.created_at, media_event_at) if value is not None)


def set_media_asset_publication(
    db: Session,
    *,
    report: models.DiamondReport,
    media_asset: models.MediaAsset,
    is_public: bool,
    actor: models.Expert,
) -> models.MediaAsset:
    """Apply an explicit admin publication decision to an eligible issued-report image."""
    if report.status != "issued":
        raise ReportDomainError("Only media of issued reports can be published")
    if media_asset.asset_type not in PUBLIC_MEDIA_ASSET_TYPES or media_asset.mime_type not in PUBLIC_MEDIA_MIME_TYPES:
        raise ReportDomainError("Only stone photos and plotting diagrams with a supported image type can be public")
    if media_asset.is_public == is_public:
        return media_asset
    media_asset.is_public = is_public
    _append_report_event(
        db,
        report_id=report.report_id,
        action="media_published" if is_public else "media_unpublished",
        actor_id=actor.expert_id,
        from_status=report.status,
        to_status=report.status,
        reason=f"{media_asset.asset_type} · #{media_asset.media_id}",
    )
    db.commit()
    db.refresh(media_asset)
    return media_asset


def create_media_asset(
    db: Session,
    *,
    report_id: str,
    uploaded_by_id: int,
    asset_type: str,
    storage_data: dict[str, object],
) -> models.MediaAsset:
    asset = models.MediaAsset(
        report_id=report_id,
        uploaded_by_id=uploaded_by_id,
        asset_type=asset_type,
        is_public=False,
        **storage_data,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def delete_media_asset(db: Session, asset: models.MediaAsset) -> None:
    db.delete(asset)
    db.commit()


def get_reference_values(db: Session, category: str | None = None) -> list[models.ReferenceValue]:
    query = db.query(models.ReferenceValue).filter(models.ReferenceValue.is_active.is_(True))
    if category:
        query = query.filter(models.ReferenceValue.category == category)
    return query.order_by(models.ReferenceValue.category, models.ReferenceValue.sort_order, models.ReferenceValue.code).all()

# Отримати користувача за логіном (для авторизації)
def get_user_by_username(db: Session, username: str):
    return db.query(models.Expert).filter(models.Expert.username == username).first()


def get_user_by_id(db: Session, expert_id: int) -> models.Expert | None:
    return db.query(models.Expert).filter(models.Expert.expert_id == expert_id).first()

# Отримати всіх користувачів (для адміна - /users/)
def get_all_users(db: Session, search: str | None, page: int, page_size: int):
    query = db.query(models.Expert)
    if search:
        like_value = f"%{search.strip()}%"
        query = query.filter(
            models.Expert.username.ilike(like_value)
            | models.Expert.first_name.ilike(like_value)
            | models.Expert.last_name.ilike(like_value)
        )
    total = query.count()
    return query.order_by(models.Expert.username).offset((page - 1) * page_size).limit(page_size).all(), total

# Створення користувача
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.Expert(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Оновлення даних користувача (пароль або роль)
def update_user(db: Session, expert_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.Expert).filter(models.Expert.expert_id == expert_id).first()
    if not db_user:
        return None
    
    # Якщо прийшов новий пароль - хешуємо його
    for field in ("username", "first_name", "last_name", "middle_name", "role"):
        value = getattr(user_update, field)
        if value is not None:
            setattr(db_user, field, value)
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)
    
    # Якщо прийшла нова роль - оновлюємо
        
    db.commit()
    db.refresh(db_user)
    return db_user

# Видалення користувача
def update_own_profile(db: Session, user: models.Expert, profile: schemas.ProfileUpdate) -> models.Expert:
    if profile.username is not None:
        user.username = profile.username
    user.first_name = profile.first_name
    user.last_name = profile.last_name
    user.middle_name = profile.middle_name
    db.commit()
    db.refresh(user)
    return user


def update_own_password(db: Session, user: models.Expert, password_update: schemas.PasswordUpdate) -> bool:
    if not verify_password(password_update.current_password, user.password_hash):
        return False
    user.password_hash = get_password_hash(password_update.new_password)
    db.commit()
    return True


def set_user_active(db: Session, expert_id: int, is_active: bool) -> models.Expert | None:
    user = get_user_by_id(db, expert_id)
    if user is None:
        return None
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

# Отримати тільки гемологів (фільтр по ролі - /experts/)
def get_active_experts(db: Session):
    return db.query(models.Expert).filter(
        models.Expert.role != 'admin', models.Expert.is_active.is_(True)
    ).all()

def _period_bounds(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
    """Return UTC-like half-open bounds for date-only operational filters."""
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ReportDomainError("date_from must not be after date_to")
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc) if date_to else None
    return start, end


def _work_session_record(session: models.ReportWorkSession) -> schemas.WorkSessionDurationRecord:
    return schemas.WorkSessionDurationRecord(
        report_id=session.report_id,
        duration_seconds=session.active_seconds,
        finished_at=session.ended_at,
    )


def get_expert_stats(db: Session, *, date_from: date | None = None, date_to: date | None = None) -> list[schemas.ExpertStats]:
    """Return admin-only report counts and finished, server-timed work sessions."""
    start, end = _period_bounds(date_from, date_to)
    report_join = and_(
        models.DiamondReport.expert_id == models.Expert.expert_id,
        models.DiamondReport.record_scope == "operational",
    )
    if start is not None:
        report_join = and_(report_join, models.DiamondReport.created_at >= start)
    if end is not None:
        report_join = and_(report_join, models.DiamondReport.created_at < end)
    report_query = db.query(
        models.Expert.expert_id.label("expert_id"),
        models.Expert.username.label("expert_username"),
        models.Expert.first_name.label("first_name"),
        models.Expert.last_name.label("last_name"),
        models.Expert.middle_name.label("middle_name"),
        models.Expert.is_active.label("is_active"),
        func.count(models.DiamondReport.report_id).label("total_reports"),
        func.sum(case((models.DiamondReport.status == "draft", 1), else_=0)).label("draft_reports"),
        func.sum(case((models.DiamondReport.status == "review", 1), else_=0)).label("review_reports"),
        func.sum(case((models.DiamondReport.status == "issued", 1), else_=0)).label("issued_reports"),
        func.sum(case((models.DiamondReport.status == "void", 1), else_=0)).label("void_reports"),
    ).outerjoin(
        models.DiamondReport, report_join,
    ).filter(
        models.Expert.role == "gemologist",
    ).group_by(
        models.Expert.expert_id,
        models.Expert.username,
        models.Expert.first_name,
        models.Expert.last_name,
        models.Expert.middle_name,
        models.Expert.is_active,
    )
    report_rows = report_query.order_by(models.Expert.username.asc()).all()

    sessions_query = (
        db.query(models.ReportWorkSession)
        .join(models.DiamondReport, models.ReportWorkSession.report_id == models.DiamondReport.report_id)
        .filter(
            models.ReportWorkSession.ended_at.is_not(None),
            models.DiamondReport.record_scope == "operational",
        )
    )
    if start is not None:
        sessions_query = sessions_query.filter(models.ReportWorkSession.ended_at >= start)
    if end is not None:
        sessions_query = sessions_query.filter(models.ReportWorkSession.ended_at < end)
    sessions_by_expert: dict[int, list[models.ReportWorkSession]] = {}
    for session in sessions_query.all():
        sessions_by_expert.setdefault(session.expert_id, []).append(session)

    timings_query = db.query(
        models.DiamondReport.expert_id,
        models.DiamondReport.time_to_first_save_seconds,
    ).filter(
        models.DiamondReport.time_to_first_save_seconds.is_not(None),
        models.DiamondReport.record_scope == "operational",
    )
    if start is not None:
        timings_query = timings_query.filter(models.DiamondReport.created_at >= start)
    if end is not None:
        timings_query = timings_query.filter(models.DiamondReport.created_at < end)
    timings_by_expert: dict[int, list[int]] = {}
    for expert_id, seconds in timings_query.all():
        timings_by_expert.setdefault(expert_id, []).append(seconds)

    rows: list[schemas.ExpertStats] = []
    for row in report_rows:
        sessions = sessions_by_expert.get(row.expert_id, [])
        durations = [session.active_seconds for session in sessions]
        first_save_durations = timings_by_expert.get(row.expert_id, [])
        records = [_work_session_record(session) for session in sessions]
        rows.append(schemas.ExpertStats(
            expert_id=row.expert_id, expert_username=row.expert_username,
            first_name=row.first_name, last_name=row.last_name, middle_name=row.middle_name,
            is_active=row.is_active, total_reports=row.total_reports,
            draft_reports=row.draft_reports or 0, review_reports=row.review_reports or 0,
            issued_reports=row.issued_reports or 0, void_reports=row.void_reports or 0,
            completed_work_sessions=len(records), total_active_seconds=sum(durations),
            avg_active_seconds=round(sum(durations) / len(durations)) if durations else None,
            median_active_seconds=round(median(durations)) if durations else None,
            completed_first_save_timings=len(first_save_durations),
            total_time_to_first_save_seconds=sum(first_save_durations),
            avg_time_to_first_save_seconds=round(sum(first_save_durations) / len(first_save_durations)) if first_save_durations else None,
            median_time_to_first_save_seconds=round(median(first_save_durations)) if first_save_durations else None,
            shortest_work_sessions=sorted(records, key=lambda item: (item.duration_seconds, item.report_id))[:3],
            longest_work_sessions=sorted(records, key=lambda item: (-item.duration_seconds, item.report_id))[:3],
        ))
    return rows


def start_wizard_work_session(
    db: Session,
    *,
    actor: models.Expert,
    signal: schemas.WizardWorkSessionStart,
) -> schemas.WizardWorkSessionState:
    """Start or resume the only live pre-save wizard lease for a gemologist."""
    if actor.role != "gemologist":
        raise ReportDomainError("Only gemologists can record wizard preparation time")
    now = datetime.now(timezone.utc)
    db.query(models.WizardWorkSession).filter(models.WizardWorkSession.expires_at <= now).delete(
        synchronize_session=False,
    )
    existing = db.query(models.WizardWorkSession).filter(
        models.WizardWorkSession.expert_id == actor.expert_id,
    ).with_for_update().one_or_none()
    if existing is not None and existing.tab_id == signal.tab_id:
        return schemas.WizardWorkSessionState(wizard_session_id=existing.wizard_session_id)
    if existing is not None:
        db.delete(existing)
        db.flush()
    session = models.WizardWorkSession(
        wizard_session_id=str(uuid.uuid4()),
        expert_id=actor.expert_id,
        tab_id=signal.tab_id,
        started_at=now,
        expires_at=now + timedelta(seconds=WIZARD_WORK_SESSION_LEASE_SECONDS),
    )
    db.add(session)
    db.flush()
    return schemas.WizardWorkSessionState(wizard_session_id=session.wizard_session_id)


def _attach_wizard_first_save_timing(
    db: Session,
    *,
    report: models.DiamondReport,
    author: models.Expert,
    wizard_session_id: str | None,
    now: datetime,
) -> None:
    if wizard_session_id is None:
        return
    session = db.query(models.WizardWorkSession).filter(
        models.WizardWorkSession.wizard_session_id == wizard_session_id,
        models.WizardWorkSession.expert_id == author.expert_id,
    ).with_for_update().one_or_none()
    if session is None or session.expires_at.replace(tzinfo=timezone.utc) <= now:
        return
    started_at = session.started_at.replace(tzinfo=timezone.utc) if session.started_at.tzinfo is None else session.started_at
    report.first_save_started_at = started_at
    report.time_to_first_save_seconds = max(0, round((now - started_at).total_seconds()))
    db.delete(session)


def _append_work_session_event(db: Session, session: models.ReportWorkSession, action: str, now: datetime) -> None:
    db.add(models.ReportWorkSessionEvent(
        work_session_id=session.work_session_id,
        action=action,
        recorded_at=now,
        active_seconds=session.active_seconds,
    ))


def _accrue_work_session(session: models.ReportWorkSession, now: datetime) -> None:
    last_activity = session.last_activity_at
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
    elapsed = max(0, min(WORK_SESSION_MAX_INTERVAL_SECONDS, round((now - last_activity).total_seconds())))
    session.active_seconds += elapsed
    session.last_activity_at = now


def _finish_work_session(db: Session, session: models.ReportWorkSession, *, reason: str, now: datetime) -> None:
    _accrue_work_session(session, now)
    session.ended_at = now
    session.end_reason = reason
    _append_work_session_event(db, session, "finish" if reason == "finish" else "pause", now)


def record_work_session_signal(
    db: Session,
    *,
    report: models.DiamondReport,
    actor: models.Expert,
    signal: schemas.ReportWorkSessionSignal,
) -> schemas.ReportWorkSessionState:
    """Accept a server-timed draft signal, ensuring one active tab per report owner."""
    if actor.role != "gemologist" or report.expert_id != actor.expert_id or report.status != "draft":
        raise ReportDomainError("Only the draft owner can record work time")
    now = datetime.now(timezone.utc)
    lease = db.query(models.ReportWorkSessionLease).filter(
        models.ReportWorkSessionLease.report_id == report.report_id,
        models.ReportWorkSessionLease.expert_id == actor.expert_id,
    ).with_for_update().one_or_none()
    if lease is not None and lease.expires_at.replace(tzinfo=timezone.utc) <= now:
        expired = db.get(models.ReportWorkSession, lease.work_session_id)
        if expired is not None and expired.ended_at is None:
            _finish_work_session(db, expired, reason="timeout", now=now)
        db.delete(lease)
        lease = None

    if signal.action in {"start", "resume"}:
        if lease is not None:
            prior = db.get(models.ReportWorkSession, lease.work_session_id)
            if prior is not None and prior.ended_at is None and lease.tab_id != signal.tab_id:
                _finish_work_session(db, prior, reason="replaced", now=now)
                db.delete(lease)
                lease = None
            elif prior is not None and prior.ended_at is None:
                _accrue_work_session(prior, now)
                lease.expires_at = now + timedelta(seconds=WORK_SESSION_LEASE_SECONDS)
                _append_work_session_event(db, prior, signal.action, now)
                return schemas.ReportWorkSessionState(work_session_id=prior.work_session_id, active_seconds=prior.active_seconds, is_active=True)
        session = models.ReportWorkSession(
            work_session_id=str(uuid.uuid4()), report_id=report.report_id, expert_id=actor.expert_id,
            tab_id=signal.tab_id, started_at=now, last_activity_at=now, active_seconds=0,
        )
        db.add(session)
        db.flush()
        db.add(models.ReportWorkSessionLease(
            report_id=report.report_id, expert_id=actor.expert_id, work_session_id=session.work_session_id,
            tab_id=signal.tab_id, expires_at=now + timedelta(seconds=WORK_SESSION_LEASE_SECONDS),
        ))
        _append_work_session_event(db, session, signal.action, now)
        return schemas.ReportWorkSessionState(work_session_id=session.work_session_id, active_seconds=0, is_active=True)

    if lease is None or lease.tab_id != signal.tab_id:
        raise ReportDomainError("The work session is no longer active in this tab")
    session = db.get(models.ReportWorkSession, lease.work_session_id)
    if session is None or session.ended_at is not None:
        raise ReportDomainError("The work session is no longer active")
    _accrue_work_session(session, now)
    _append_work_session_event(db, session, signal.action, now)
    if signal.action == "pause":
        session.ended_at = now
        session.end_reason = "pause"
        db.delete(lease)
        return schemas.ReportWorkSessionState(work_session_id=session.work_session_id, active_seconds=session.active_seconds, is_active=False)
    lease.expires_at = now + timedelta(seconds=WORK_SESSION_LEASE_SECONDS)
    return schemas.ReportWorkSessionState(work_session_id=session.work_session_id, active_seconds=session.active_seconds, is_active=True)


def finish_active_work_session(db: Session, *, report: models.DiamondReport, reason: str = "finish") -> None:
    """Close an owner's active session when a draft is submitted for review."""
    if report.expert_id is None:
        return
    lease = db.query(models.ReportWorkSessionLease).filter(
        models.ReportWorkSessionLease.report_id == report.report_id,
        models.ReportWorkSessionLease.expert_id == report.expert_id,
    ).one_or_none()
    if lease is None:
        return
    session = db.get(models.ReportWorkSession, lease.work_session_id)
    if session is not None and session.ended_at is None:
        _finish_work_session(db, session, reason=reason, now=datetime.now(timezone.utc))
    db.delete(lease)


def _duration_seconds(started_at: datetime, completed_at: datetime) -> int:
    """Calculate a non-negative duration across legacy naive and UTC datetimes."""
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)
    return max(0, round((completed_at - started_at).total_seconds()))


def get_admin_review_stats(db: Session, *, date_from: date | None = None, date_to: date | None = None) -> schemas.AdminReviewStatisticsResponse:
    """Summarize completed review cycles by administrator, not active work time."""
    start, end = _period_bounds(date_from, date_to)
    admins = db.query(models.Expert).filter(models.Expert.role == "admin").order_by(models.Expert.username).all()
    admin_ids = {admin.expert_id for admin in admins}
    review_starts: dict[str, datetime] = {}
    decisions: dict[int, list[schemas.ReviewDurationRecord]] = {admin.expert_id: [] for admin in admins}
    events = (
        db.query(models.ReportEvent)
        .join(models.DiamondReport, models.ReportEvent.report_id == models.DiamondReport.report_id)
        .filter(models.DiamondReport.record_scope == "operational")
        .order_by(models.ReportEvent.report_id, models.ReportEvent.event_id)
        .all()
    )
    for event in events:
        if event.to_status == "review" and event.created_at is not None:
            review_starts[event.report_id] = event.created_at
            continue
        if event.from_status != "review" or event.actor_id not in admin_ids or event.created_at is None:
            continue
        started_at = review_starts.pop(event.report_id, None)
        if started_at is None or event.to_status not in {"draft", "issued", "void"}:
            continue
        event_created_at = event.created_at if event.created_at.tzinfo else event.created_at.replace(tzinfo=timezone.utc)
        if start is not None and event_created_at < start:
            continue
        if end is not None and event_created_at >= end:
            continue
        decisions[event.actor_id].append(schemas.ReviewDurationRecord(
            report_id=event.report_id,
            decision=event.to_status,
            duration_seconds=_duration_seconds(started_at, event.created_at),
            decided_at=event.created_at,
        ))

    pending_starts = [
        review_starts[report.report_id]
        for report in db.query(models.DiamondReport).filter(
            models.DiamondReport.status == "review",
            models.DiamondReport.record_scope == "operational",
        ).all()
        if report.report_id in review_starts
    ]
    rows: list[schemas.AdminReviewStats] = []
    for admin in admins:
        admin_decisions = decisions[admin.expert_id]
        durations = [item.duration_seconds for item in admin_decisions]
        rows.append(schemas.AdminReviewStats(
            admin_id=admin.expert_id,
            admin_username=admin.username,
            first_name=admin.first_name,
            last_name=admin.last_name,
            middle_name=admin.middle_name,
            is_active=admin.is_active,
            completed_reviews=len(admin_decisions),
            returned_to_draft=sum(item.decision == "draft" for item in admin_decisions),
            issued_reports=sum(item.decision == "issued" for item in admin_decisions),
            voided_reports=sum(item.decision == "void" for item in admin_decisions),
            avg_review_duration_seconds=round(sum(durations) / len(durations)) if durations else None,
            median_review_duration_seconds=round(median(durations)) if durations else None,
            shortest_reviews=sorted(admin_decisions, key=lambda item: (item.duration_seconds, item.report_id))[:3],
            longest_reviews=sorted(admin_decisions, key=lambda item: (-item.duration_seconds, item.report_id))[:3],
        ))
    return schemas.AdminReviewStatisticsResponse(
        admins=rows,
        pending_review_count=len(pending_starts),
        oldest_review_started_at=min(pending_starts) if pending_starts else None,
    )

def get_mappings(db: Session, category: str = None):
    """
    Отримує список мапінгів (довідників) з бази Market.
    
    :param category: (Optional) Фільтр по категорії (напр. 'clarity'). 
                     Якщо None - повертає всі довідники.
    """
    query = db.query(models.GradeMapping)
    if category:
        query = query.filter(models.GradeMapping.category == category)
    # Сортуємо по category, а потім по значенню (щоб D йшло перед E)
    return query.order_by(models.GradeMapping.category, models.GradeMapping.grade_value).all()

# Отримати найсвіжішу ринкову ціну
def get_latest_market_price(db: Session):
    return db.query(models.MarketPriceRef).order_by(models.MarketPriceRef.id.desc()).first()

# Створити новий запис про ціну (Історія змін)
def create_market_price(db: Session, price_data: schemas.MarketPriceCreate, admin_id: int):
    db_price = models.MarketPriceRef(
        price_index_value=price_data.price_index_value,
        updated_by=admin_id,
        notes=price_data.notes
    )
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def get_market_data_providers(db: Session) -> list[models.MarketDataProvider]:
    return (
        db.query(models.MarketDataProvider)
        .filter(models.MarketDataProvider.is_active.is_(True))
        .order_by(models.MarketDataProvider.display_name)
        .all()
    )


def get_market_reference_policy(db: Session) -> models.MarketReferencePolicy | None:
    """Return the single policy that controls only future automatic references."""
    return db.get(models.MarketReferencePolicy, 1)


def update_market_reference_policy(
    db: Session,
    *,
    payload: schemas.MarketReferencePolicyUpdate,
    actor: models.Expert,
) -> models.MarketReferencePolicy:
    """Validate selected provider capabilities before replacing the future-only policy."""
    market_provider = None
    if payload.market_provider_code is not None:
        market_provider = db.get(models.MarketDataProvider, payload.market_provider_code)
        if market_provider is None or not market_provider.is_active:
            raise ReportDomainError("Selected market-data provider is unavailable")
        if market_provider.provider_type != "market_reference":
            raise ReportDomainError("Selected provider cannot supply a market reference")
    fx_provider = None
    if payload.use_fx_conversion:
        if payload.fx_provider_code is None:
            raise ReportDomainError("Select an FX provider when UAH conversion is enabled")
        fx_provider = db.get(models.MarketDataProvider, payload.fx_provider_code)
        if fx_provider is None or not fx_provider.is_active:
            raise ReportDomainError("Selected FX provider is unavailable")
        if fx_provider.provider_type != "fx_reference":
            raise ReportDomainError("Selected provider cannot supply an FX rate")
    policy = get_market_reference_policy(db)
    if policy is None:
        policy = models.MarketReferencePolicy(policy_id=1)
        db.add(policy)
    policy.market_provider_code = market_provider.provider_code if market_provider else None
    policy.use_fx_conversion = payload.use_fx_conversion
    policy.fx_provider_code = fx_provider.provider_code if fx_provider else None
    policy.updated_by_id = actor.expert_id
    db.commit()
    db.refresh(policy)
    return policy


def get_market_data_snapshots(db: Session) -> list[models.MarketDataSnapshot]:
    return (
        db.query(models.MarketDataSnapshot)
        .order_by(models.MarketDataSnapshot.created_at.desc(), models.MarketDataSnapshot.snapshot_id.desc())
        .all()
    )


def get_fx_data_snapshots(db: Session) -> list[models.FxDataSnapshot]:
    return (
        db.query(models.FxDataSnapshot)
        .filter(models.FxDataSnapshot.provider_code == "nbu")
        .order_by(models.FxDataSnapshot.retrieved_at.desc(), models.FxDataSnapshot.fx_snapshot_id.desc())
        .all()
    )


def get_market_provider_schedules(db: Session) -> list[models.MarketProviderSchedule]:
    return (
        db.query(models.MarketProviderSchedule)
        .order_by(models.MarketProviderSchedule.provider_code)
        .all()
    )


def get_market_provider_schedule(
    db: Session, provider_code: str,
) -> models.MarketProviderSchedule | None:
    return db.get(models.MarketProviderSchedule, provider_code)


def update_market_provider_schedule(
    db: Session,
    *,
    payload: schemas.MarketProviderScheduleUpdate,
    actor: models.Expert,
) -> models.MarketProviderSchedule:
    schedule = get_market_provider_schedule(db, payload.provider_code)
    provider = db.get(models.MarketDataProvider, payload.provider_code)
    if schedule is None or provider is None:
        raise ReportDomainError("Market provider schedule is not registered")
    if payload.block_after_hours < payload.warn_after_hours:
        raise ReportDomainError("Block freshness threshold cannot be earlier than warning threshold")
    schedule.enabled = payload.enabled
    schedule.scheduled_hour = payload.scheduled_hour
    schedule.scheduled_minute = payload.scheduled_minute
    schedule.warn_after_hours = payload.warn_after_hours
    schedule.block_after_hours = payload.block_after_hours
    schedule.updated_by_id = actor.expert_id
    db.commit()
    db.refresh(schedule)
    return schedule


def get_market_provider_operations(
    db: Session, *, limit: int = 50,
) -> list[models.MarketProviderOperation]:
    return (
        db.query(models.MarketProviderOperation)
        .order_by(
            models.MarketProviderOperation.completed_at.desc(),
            models.MarketProviderOperation.operation_id.desc(),
        )
        .limit(limit)
        .all()
    )


def create_market_provider_operation(
    db: Session,
    *,
    provider_code: str,
    trigger_type: str,
    status: str,
    attempt_number: int,
    started_at: datetime,
    completed_at: datetime,
    message: str | None = None,
    market_snapshot_id: int | None = None,
    fx_snapshot_id: int | None = None,
    actor: models.Expert | None = None,
) -> models.MarketProviderOperation:
    operation = models.MarketProviderOperation(
        provider_code=provider_code,
        trigger_type=trigger_type,
        status=status,
        attempt_number=attempt_number,
        started_at=started_at,
        completed_at=completed_at,
        message=message,
        market_snapshot_id=market_snapshot_id,
        fx_snapshot_id=fx_snapshot_id,
        initiated_by_id=actor.expert_id if actor else None,
    )
    db.add(operation)
    db.commit()
    db.refresh(operation)
    return operation


def latest_provider_retrieved_at(
    db: Session, provider_code: str,
) -> datetime | None:
    if provider_code == "nbu":
        snapshot = (
            db.query(models.FxDataSnapshot)
            .filter(models.FxDataSnapshot.provider_code == provider_code)
            .order_by(models.FxDataSnapshot.retrieved_at.desc(), models.FxDataSnapshot.fx_snapshot_id.desc())
            .first()
        )
        return snapshot.retrieved_at if snapshot else None
    snapshot = (
        db.query(models.MarketDataSnapshot)
        .filter(
            models.MarketDataSnapshot.provider_code == provider_code,
            models.MarketDataSnapshot.status == "approved",
        )
        .order_by(models.MarketDataSnapshot.approved_at.desc(), models.MarketDataSnapshot.snapshot_id.desc())
        .first()
    )
    return snapshot.retrieved_at if snapshot else None


def get_latest_fresh_fx_snapshot(
    db: Session, *, provider_code: str, max_age_hours: int, now: datetime,
) -> models.FxDataSnapshot | None:
    snapshot = (
        db.query(models.FxDataSnapshot)
        .filter(models.FxDataSnapshot.provider_code == provider_code)
        .order_by(models.FxDataSnapshot.retrieved_at.desc(), models.FxDataSnapshot.fx_snapshot_id.desc())
        .first()
    )
    if snapshot is None:
        return None
    retrieved_at = snapshot.retrieved_at
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
    if now - retrieved_at > timedelta(hours=max_age_hours):
        return None
    return snapshot


def create_nbu_fx_snapshot(
    db: Session, *, fetched: NbuUsdUahRate, actor: models.Expert | None, commit: bool,
) -> models.FxDataSnapshot:
    provider = db.get(models.MarketDataProvider, "nbu")
    if provider is None or not provider.is_active:
        raise ReportDomainError("NBU FX provider is not registered or active")
    snapshot = models.FxDataSnapshot(
        provider_code="nbu",
        base_currency_code="USD",
        quote_currency_code="UAH",
        rate=fetched.rate,
        rate_date=fetched.rate_date,
        source_url=fetched.source_url,
        retrieved_at=fetched.retrieved_at,
        created_by_id=actor.expert_id if actor else None,
    )
    db.add(snapshot)
    db.flush()
    if commit:
        db.commit()
        db.refresh(snapshot)
    return snapshot


def get_market_data_snapshot(db: Session, snapshot_id: int) -> models.MarketDataSnapshot | None:
    return db.get(models.MarketDataSnapshot, snapshot_id)


def market_snapshot_checksum(fetched: FetchedMarketSnapshot) -> str:
    canonical_lines = [
        f"{quote.shape_code}|{quote.carat_anchor}|{quote.color_code}|{quote.clarity_code}|{quote.price_per_carat}"
        for quote in sorted(
            fetched.quotes,
            key=lambda item: (item.shape_code, item.carat_anchor, item.color_code, item.clarity_code),
        )
    ]
    return hashlib.sha256("\n".join(canonical_lines).encode("utf-8")).hexdigest()


def create_market_data_candidate(
    db: Session,
    *,
    fetched: FetchedMarketSnapshot,
    actor: models.Expert | None,
) -> models.MarketDataSnapshot:
    provider = db.get(models.MarketDataProvider, fetched.provider_code)
    if provider is None or not provider.is_active:
        raise ReportDomainError("Market-data provider is not registered or active")
    snapshot = models.MarketDataSnapshot(
        provider_code=fetched.provider_code,
        snapshot_kind="market_reference",
        status="candidate",
        currency_code=fetched.currency_code,
        unit=fetched.unit,
        source_url=fetched.source_url,
        methodology_url=fetched.methodology_url,
        coverage_note=fetched.coverage_note,
        quote_count=len(fetched.quotes),
        content_sha256=market_snapshot_checksum(fetched),
        retrieved_at=fetched.retrieved_at,
        created_by_id=actor.expert_id if actor else None,
    )
    db.add(snapshot)
    db.flush()
    db.add_all(
        models.MarketDataQuote(
            snapshot_id=snapshot.snapshot_id,
            shape_code=quote.shape_code,
            carat_anchor=quote.carat_anchor,
            color_code=quote.color_code,
            clarity_code=quote.clarity_code,
            price_per_carat=quote.price_per_carat,
        )
        for quote in fetched.quotes
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot


def decide_market_data_snapshot(
    db: Session,
    *,
    snapshot: models.MarketDataSnapshot,
    approve: bool,
    actor: models.Expert,
    reason: str | None,
) -> models.MarketDataSnapshot:
    if snapshot.status != "candidate":
        raise ReportDomainError("Only a candidate snapshot can be decided")
    snapshot.status = "approved" if approve else "rejected"
    snapshot.approved_by_id = actor.expert_id
    snapshot.approved_at = datetime.now(timezone.utc)
    snapshot.decision_reason = reason
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_report_valuations(db: Session, report: models.DiamondReport) -> list[models.StoneValuation]:
    if report.stone_id is None:
        return []
    return (
        db.query(models.StoneValuation)
        .filter(models.StoneValuation.stone_id == report.stone_id)
        .order_by(models.StoneValuation.created_at.desc(), models.StoneValuation.valuation_id.desc())
        .all()
    )


def _grade_label(db: Session, category: str, grade: int | None) -> str | None:
    if grade is None:
        return None
    mapping = (
        db.query(models.GradeMapping)
        .filter(models.GradeMapping.category == category, models.GradeMapping.grade_value == grade)
        .one_or_none()
    )
    return mapping.grade_label.upper() if mapping else None


def _openfacet_price_per_carat(
    db: Session,
    *,
    snapshot_id: int,
    stone: models.Stone,
) -> tuple[Decimal, str]:
    """Interpolate an approved OpenFacet snapshot only within known anchors."""
    if stone.origin != "natural":
        raise ReportDomainError("OpenFacet reference is available only for natural stones")
    shape_code = stone.shape.strip().lower()
    color_code = _grade_label(db, "color", stone.color_grade)
    clarity_code = _grade_label(db, "clarity", stone.clarity_grade)
    if not color_code or not clarity_code or stone.carat_weight is None:
        raise ReportDomainError("The report lacks characteristics required by the selected market snapshot")
    quotes = (
        db.query(models.MarketDataQuote)
        .filter(
            models.MarketDataQuote.snapshot_id == snapshot_id,
            models.MarketDataQuote.shape_code == shape_code,
            models.MarketDataQuote.color_code == color_code,
            models.MarketDataQuote.clarity_code == clarity_code,
        )
        .order_by(models.MarketDataQuote.carat_anchor)
        .all()
    )
    if not quotes:
        raise ReportDomainError("The approved snapshot does not cover this shape, color or clarity")
    carat_weight = Decimal(stone.carat_weight)
    lower = next((quote for quote in reversed(quotes) if Decimal(quote.carat_anchor) <= carat_weight), None)
    upper = next((quote for quote in quotes if Decimal(quote.carat_anchor) >= carat_weight), None)
    if lower is None or upper is None:
        raise ReportDomainError("The approved snapshot does not cover this carat weight")
    lower_price = Decimal(lower.price_per_carat)
    upper_price = Decimal(upper.price_per_carat)
    if Decimal(lower.carat_anchor) == Decimal(upper.carat_anchor):
        return lower_price, shape_code
    share = (carat_weight - Decimal(lower.carat_anchor)) / (
        Decimal(upper.carat_anchor) - Decimal(lower.carat_anchor)
    )
    price = ((Decimal("1") - share) * lower_price.ln() + share * upper_price.ln()).exp()
    return price.quantize(Decimal("0.01")), shape_code


@dataclass(frozen=True)
class SystemMarketReferenceCandidate:
    """A reproducible automatic OpenFacet reference ready for FX conversion."""

    snapshot: models.MarketDataSnapshot
    amount: Decimal
    source_reference: str


def prepare_system_market_reference(
    db: Session, *, report: models.DiamondReport, provider_code: str,
) -> SystemMarketReferenceCandidate | None:
    """Return an applicable automatic reference, without treating a gap as an error."""
    if report.stone is None or report.stone_id is None:
        return None
    return prepare_system_market_reference_for_stone(db, stone=report.stone, provider_code=provider_code)


def prepare_system_market_reference_for_stone(
    db: Session, *, stone: models.Stone, provider_code: str,
) -> SystemMarketReferenceCandidate | None:
    """Build a policy-provider preview or valuation candidate for one stone."""
    snapshot = (
        db.query(models.MarketDataSnapshot)
        .filter(
            models.MarketDataSnapshot.provider_code == provider_code,
            models.MarketDataSnapshot.snapshot_kind == "market_reference",
            models.MarketDataSnapshot.status == "approved",
        )
        .order_by(
            models.MarketDataSnapshot.approved_at.desc(),
            models.MarketDataSnapshot.snapshot_id.desc(),
        )
        .first()
    )
    if snapshot is None:
        return None
    try:
        if provider_code != "openfacet":
            return None
        price_per_carat, shape_code = _openfacet_price_per_carat(db, snapshot_id=snapshot.snapshot_id, stone=stone)
    except ReportDomainError:
        return None
    amount = (price_per_carat * Decimal(stone.carat_weight)).quantize(Decimal("0.01"))
    return SystemMarketReferenceCandidate(
        snapshot=snapshot,
        amount=amount,
        source_reference=(
            f"snapshot:{snapshot.snapshot_id}; shape:{shape_code}; "
            f"USD/ct:{price_per_carat}; automatic:latest-approved"
        ),
    )


def attach_system_market_reference(
    db: Session,
    *,
    report: models.DiamondReport,
    candidate: SystemMarketReferenceCandidate,
    actor: models.Expert,
    fx_snapshot: models.FxDataSnapshot | None,
) -> models.StoneValuation | None:
    """Persist one immutable system reference unless the same inputs were saved already."""
    if report.stone_id is None:
        return None
    existing = (
        db.query(models.StoneValuation)
        .filter(
            models.StoneValuation.stone_id == report.stone_id,
            models.StoneValuation.valuation_kind == "system_market_reference",
            models.StoneValuation.market_snapshot_id == candidate.snapshot.snapshot_id,
            models.StoneValuation.amount == candidate.amount,
            models.StoneValuation.source_reference == candidate.source_reference,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing
    valuation = models.StoneValuation(
        stone_id=report.stone_id,
        valuation_kind="system_market_reference",
        amount=candidate.amount,
        currency_code=candidate.snapshot.currency_code,
        unit="TOTAL_STONE",
        source_name="OpenFacet" if candidate.snapshot.provider_code == "openfacet" else candidate.snapshot.provider_code,
        source_reference=candidate.source_reference,
        market_snapshot_id=candidate.snapshot.snapshot_id,
        applicability_note=None,
        fx_snapshot_id=fx_snapshot.fx_snapshot_id if fx_snapshot else None,
        fx_rate=fx_snapshot.rate if fx_snapshot else None,
        fx_rate_date=fx_snapshot.rate_date if fx_snapshot else None,
        converted_amount=convert_usd_to_uah(candidate.amount, Decimal(fx_snapshot.rate)) if fx_snapshot else None,
        converted_currency_code="UAH" if fx_snapshot else None,
        observed_at=candidate.snapshot.retrieved_at,
        created_by_id=actor.expert_id,
    )
    db.add(valuation)
    _append_report_event(
        db,
        report_id=report.report_id,
        action="system_market_reference_added",
        actor_id=actor.expert_id,
        from_status=None,
        to_status=None,
        reason=_market_reference_event_reason(valuation),
    )
    db.commit()
    db.refresh(valuation)
    return valuation


def system_market_reference_exists(
    db: Session, *, report: models.DiamondReport, candidate: SystemMarketReferenceCandidate,
) -> bool:
    """Check idempotency before attaching a stored provider snapshot."""
    if report.stone_id is None:
        return False
    return (
        db.query(models.StoneValuation.valuation_id)
        .filter(
            models.StoneValuation.stone_id == report.stone_id,
            models.StoneValuation.valuation_kind == "system_market_reference",
            models.StoneValuation.market_snapshot_id == candidate.snapshot.snapshot_id,
            models.StoneValuation.amount == candidate.amount,
            models.StoneValuation.source_reference == candidate.source_reference,
        )
        .first()
        is not None
    )


def attach_market_reference(
    db: Session,
    *,
    report: models.DiamondReport,
    request: schemas.MarketReferenceAttachRequest,
    actor: models.Expert,
    fx_snapshot: models.FxDataSnapshot | None,
) -> models.StoneValuation:
    if report.stone is None or report.stone_id is None:
        raise ReportDomainError("Report has no normalized stone")
    snapshot = get_market_data_snapshot(db, request.snapshot_id)
    if snapshot is None or snapshot.status != "approved":
        raise ReportDomainError("Select an approved market-data snapshot")
    if snapshot.snapshot_kind != "market_reference" or snapshot.provider_code != "openfacet":
        raise ReportDomainError("This snapshot cannot create an OpenFacet market reference")
    existing = (
        db.query(models.StoneValuation)
        .filter(
            models.StoneValuation.stone_id == report.stone_id,
            models.StoneValuation.valuation_kind == "market_reference",
            models.StoneValuation.market_snapshot_id == snapshot.snapshot_id,
        )
        .one_or_none()
    )
    if existing is not None:
        raise ReportDomainError("This approved snapshot is already attached to the report")
    price_per_carat, shape_code = _openfacet_price_per_carat(
        db, snapshot_id=snapshot.snapshot_id, stone=report.stone,
    )
    amount = (price_per_carat * Decimal(report.stone.carat_weight)).quantize(Decimal("0.01"))
    valuation = models.StoneValuation(
        stone_id=report.stone_id,
        valuation_kind="market_reference",
        amount=amount,
        currency_code=snapshot.currency_code,
        unit="TOTAL_STONE",
        source_name="OpenFacet",
        source_reference=f"snapshot:{snapshot.snapshot_id}; shape:{shape_code}; USD/ct:{price_per_carat}",
        market_snapshot_id=snapshot.snapshot_id,
        applicability_note=request.applicability_note,
        fx_snapshot_id=fx_snapshot.fx_snapshot_id if fx_snapshot else None,
        fx_rate=fx_snapshot.rate if fx_snapshot else None,
        fx_rate_date=fx_snapshot.rate_date if fx_snapshot else None,
        converted_amount=convert_usd_to_uah(amount, Decimal(fx_snapshot.rate)) if fx_snapshot else None,
        converted_currency_code="UAH" if fx_snapshot else None,
        observed_at=snapshot.retrieved_at,
        created_by_id=actor.expert_id,
    )
    db.add(valuation)
    _append_report_event(
        db,
        report_id=report.report_id,
        action="market_reference_added",
        actor_id=actor.expert_id,
        from_status=None,
        to_status=None,
        reason=_market_reference_event_reason(valuation),
    )
    db.commit()
    db.refresh(valuation)
    return valuation
