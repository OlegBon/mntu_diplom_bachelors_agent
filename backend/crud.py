from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, getcontext
import secrets

from . import models, schemas
from .security import get_password_hash, verify_password

from .calculator import DiamondCalculator


REPORT_RULE_VERSION = "idc-demo-v1"


class ReportDomainError(ValueError):
    """A controlled violation of the new report-domain contract."""


def _next_report_id(db: Session) -> str:
    last_report = db.query(models.DiamondReport).order_by(models.DiamondReport.report_id.desc()).first()
    if last_report:
        try:
            next_number = int(last_report.report_id.split("-")[1]) + 1
        except (IndexError, ValueError):
            next_number = db.query(models.DiamondReport).count() + 1
    else:
        next_number = 1
    return f"DR-{next_number:05d}"


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


def preview_report_calculation(db: Session, stone: schemas.ReportCalculationInput) -> schemas.ReportCalculationPreview:
    """Calculate the server-authoritative IDC preview without persisting data."""
    proportions = DiamondCalculator.evaluate_proportions(
        stone.table_percent,
        stone.depth_percent,
        stone.crown_angle,
        stone.pavilion_angle,
    )
    cut = DiamondCalculator.calculate_final_cut(proportions, stone.polish_grade, stone.symmetry_grade)
    demo_price = None
    market = db.query(models.MarketPriceRef).order_by(models.MarketPriceRef.id.desc()).first()
    if market and stone.carat_weight is not None and stone.color_grade is not None and stone.clarity_grade is not None:
        demo_price = (
            Decimal(market.price_index_value)
            * getcontext().power(stone.carat_weight, Decimal("1.3"))
            * (Decimal("1") - Decimal(stone.color_grade) * Decimal("0.05"))
            * (Decimal("1") - Decimal(stone.clarity_grade) * Decimal("0.07"))
            * (Decimal("1") - Decimal(cut) * Decimal("0.10"))
        ).quantize(Decimal("0.01"))
    return schemas.ReportCalculationPreview(
        system_proportions_grade=proportions,
        system_cut_grade=cut,
        calculation_rule_version=REPORT_RULE_VERSION,
        demo_price_usd=demo_price,
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
        query = query.filter(models.DiamondReport.price >= price_min)
    if price_max is not None:
        query = query.filter(models.DiamondReport.price <= price_max)
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
        "price_desc": (desc(models.DiamondReport.price), desc(models.DiamondReport.report_id)),
        "price_asc": (asc(models.DiamondReport.price), asc(models.DiamondReport.report_id)),
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
    return reports, total


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
    is_confirmed = payload.expert_proportions_grade is not None and payload.expert_cut_grade is not None
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
        calculation_rule_version=REPORT_RULE_VERSION,
        expert_proportions_grade=payload.expert_proportions_grade,
        expert_cut_grade=payload.expert_cut_grade,
        expert_confirmed_at=now if is_confirmed else None,
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
    report.calculation_rule_version = REPORT_RULE_VERSION
    report.expert_proportions_grade = payload.expert_proportions_grade
    report.expert_cut_grade = payload.expert_cut_grade
    report.expert_confirmed_at = datetime.now(timezone.utc) if (
        payload.expert_proportions_grade is not None and payload.expert_cut_grade is not None
    ) else None
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
    if target_status == "issued" and (
        report.expert_proportions_grade is None or report.expert_cut_grade is None
    ):
        raise ReportDomainError("Issued reports require expert-confirmed proportions and cut grades")

    now = datetime.now(timezone.utc)
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
        .filter(
            models.PublicPassport.report_id == report_id,
            models.PublicPassport.is_active.is_(True),
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
def get_all_users(db: Session):
    return db.query(models.Expert).order_by(models.Expert.username).all()

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
    for field in ("first_name", "last_name", "middle_name", "role"):
        value = getattr(user_update, field)
        if value is not None:
            setattr(db_user, field, value)
    
    # Якщо прийшла нова роль - оновлюємо
        
    db.commit()
    db.refresh(db_user)
    return db_user

# Видалення користувача
def update_own_profile(db: Session, user: models.Expert, profile: schemas.ProfileUpdate) -> models.Expert:
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

# Функція для отримання статистики гемологів (SQL GROUP BY)
from sqlalchemy import func
def get_expert_stats(db: Session):
    return db.query(
        models.Expert.username.label("expert_username"),
        func.count(models.DiamondReport.report_id).label("total_reports"),
        func.avg(models.DiamondReport.carat_weight).label("avg_carat")
    ).join(models.DiamondReport).group_by(models.Expert.username).all()

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
