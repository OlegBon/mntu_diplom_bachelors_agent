from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, timezone
import random

from . import models, schemas
from .security import get_password_hash

from .calculator import DiamondCalculator
from .ml_service import MLService


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
    if search:
        query = query.filter(models.DiamondReport.report_id.ilike(f"%{search.strip()}%"))

    sort_columns = {
        "report_date_desc": (desc(models.DiamondReport.report_date), desc(models.DiamondReport.report_id)),
        "report_date_asc": (asc(models.DiamondReport.report_date), asc(models.DiamondReport.report_id)),
        "report_id_asc": (asc(models.DiamondReport.report_id),),
        "report_id_desc": (desc(models.DiamondReport.report_id),),
        "carat_desc": (desc(models.Stone.carat_weight), desc(models.DiamondReport.report_id)),
        "carat_asc": (asc(models.Stone.carat_weight), asc(models.DiamondReport.report_id)),
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
) -> models.DiamondReport:
    if report.status != "draft":
        raise ReportDomainError("Only draft reports can be edited")
    if report.stone is None:
        raise ReportDomainError("Report has no normalized stone")
    _apply_stone_draft(report.stone, payload.stone)
    system_proportions, system_cut = _system_grades(payload.stone)
    report.expert_comment = payload.expert_comment
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

# Отримати всіх користувачів (для адміна - /users/)
def get_all_users(db: Session):
    return db.query(models.Expert).all()

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
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)
    
    # Якщо прийшла нова роль - оновлюємо
    if user_update.role:
        db_user.role = user_update.role
        
    db.commit()
    db.refresh(db_user)
    return db_user

# Видалення користувача
def delete_user(db: Session, expert_id: int):
    db_user = db.query(models.Expert).filter(models.Expert.expert_id == expert_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# Отримати тільки гемологів (фільтр по ролі - /experts/)
def get_active_experts(db: Session):
    return db.query(models.Expert).filter(models.Expert.role != 'admin').all()

# Отримати звіти з фільтрацією, сортуванням і пагінацією
def get_reports(
    db: Session, 
    skip: int = 0, 
    limit: int = 50,
    status: str = "all",
    sort_by: str = "newest",
    search: str = None
):
    query = db.query(models.DiamondReport)

    # 1. Фільтр по Статусу
    if status == "active":
        query = query.filter(models.DiamondReport.is_sold == False)
    elif status == "sold":
        query = query.filter(models.DiamondReport.is_sold == True)
    
    # 2. Пошук (по ID)
    if search:
        query = query.filter(models.DiamondReport.report_id.like(f"%{search}%"))

    # 3. Сортування
    if sort_by == "newest":
        # Спочатку свіжа дата, якщо дати однакові — більший ID
        query = query.order_by(desc(models.DiamondReport.report_date), desc(models.DiamondReport.report_id))
    elif sort_by == "oldest":
        # Спочатку старі, потім менші ID
        query = query.order_by(asc(models.DiamondReport.report_date), asc(models.DiamondReport.report_id))
    elif sort_by == "expensive":
        query = query.order_by(desc(models.DiamondReport.price))
    elif sort_by == "cheapest":
        query = query.order_by(asc(models.DiamondReport.price))
    else:
        # Дефолтний стан (страховка) — просто останні додані по ID
        query = query.order_by(desc(models.DiamondReport.report_id))
    
    # Сортування за замовчуванням (щоб порядок не стрибав)
    query = query.order_by(desc(models.DiamondReport.report_id))

    return query.offset(skip).limit(limit).all()

# Отримати звіт по ID
def get_diamond_report(db: Session, report_id: str):
    return db.query(models.DiamondReport).filter(models.DiamondReport.report_id == report_id).first()

# Функція для створення нового звіту
def create_diamond_report(db: Session, diamond: schemas.DiamondCreate, expert_id: int):
    # Генерація ID
    # Знаходимо останній звіт за номером (сортуємо Z -> A)
    last_report = db.query(models.DiamondReport).order_by(models.DiamondReport.report_id.desc()).first()
    
    if last_report:
        try:
            # Беремо "DR-00005", розбиваємо по "-", беремо другу частину "00005" і робимо int
            last_id_str = last_report.report_id
            last_number = int(last_id_str.split('-')[1])
            new_id_number = last_number + 1
        except (IndexError, ValueError):
            # Якщо раптом в базі ID нестандартного формату
            new_id_number = db.query(models.DiamondReport).count() + 1
    else:
        # Якщо це найперший звіт у порожній базі
        new_id_number = 1
    
    new_report_id = f"DR-{new_id_number:05d}"

    # Розрахунок proportions grade (якщо не задано вручну)
    calc_proportions = diamond.proportions_grade
    if calc_proportions is None:
        calc_proportions = DiamondCalculator.evaluate_proportions(
            diamond.table_percent, diamond.depth_percent,
            diamond.crown_angle, diamond.pavilion_angle
        )

    # Розрахунок cut grade
    calc_cut = diamond.cut_grade
    if calc_cut is None:
        calc_cut = DiamondCalculator.calculate_final_cut(
            calc_proportions, diamond.polish_grade, diamond.symmetry_grade
        )

    # Прогноз ціни (ML)
    calc_price = diamond.price
    if not calc_price or calc_price == 0:
        calc_price = MLService.predict_price(
            diamond.carat_weight, diamond.color_grade, 
            diamond.clarity_grade, calc_cut
        )

    # Створення запису
    db_diamond = models.DiamondReport(
        report_id=new_report_id,
        report_date=date.today(),
        expert_id=expert_id,
        
        # Розпаковка всіх полів схеми
        **diamond.dict(exclude={'cut_grade', 'proportions_grade', 'price'}),
        
        # Явно записуємо розраховані значення
        cut_grade=calc_cut,
        proportions_grade=calc_proportions,
        price=calc_price,
        
        # Дефолтні поля
        is_sold=False,
        # The source dataset stores this value in minutes; the OLTP schema uses
        # seconds, so preserve the same 5–40 minute demo range explicitly.
        evaluation_time_sec=random.randint(5, 40) * 60,
        report_notes_length=0,
        report_sentiment=0
    )
    
    db.add(db_diamond)
    db.commit()
    db.refresh(db_diamond)
    return db_diamond

# Функція для оновлення звіту
def update_diamond_report(
    db: Session,
    report: models.DiamondReport,
    updates: schemas.DiamondUpdate,
):
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(report, key, value)
    db.commit()
    db.refresh(report)
    return report

# Функція для видалення звіту
def delete_diamond_report(db: Session, report: models.DiamondReport):
    db.delete(report)
    db.commit()

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
