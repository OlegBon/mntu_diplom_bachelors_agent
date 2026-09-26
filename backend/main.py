from fastapi import FastAPI, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from jose import JWTError, jwt
import qrcode
from qrcode.image.svg import SvgPathImage

from . import crud, database, media_storage, models, schemas, security
from .fx import FxProviderError, fetch_nbu_usd_uah
from .market_operations import freshness_status, run_provider_operation
from .market_providers import get_market_provider
from .passport_pdf import PublicPassportPdfMedia, build_demo_passport_preview_pdf, build_public_passport_pdf

app = FastAPI(title="Diamond ID System API")

# CORS для локального Gulp/BrowserSync. Порт може змінюватися, якщо 3000 зайнятий.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Спеціальна схема, яка каже Swagger-у, де брати токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функція для отримання поточного користувача за токеном
# Ця функція буде використовуватися як Dependency в ендпоінтах, де потрібна авторизація
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Розшифровуємо токен
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Шукаємо користувача в БД
    user = crud.get_user_by_username(db, username=username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

# Авторизація - отримання токена (логін)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Шукаємо користувача в базі
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # Перевіряємо чи юзер існує і чи правильний пароль
    if not user or not user.is_active or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Якщо все ОК - генеруємо токен
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Віддаємо токен клієнту
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Diamond Identification System API is running"}

# Технічний ендпоінт (адмінський)
# Повертає список всіх користувачів
# Без токена доступ заборонено, current_user перевіряє токен
@app.get("/users/", response_model=schemas.ExpertListResponse)
def read_users(
    search: Optional[str] = Query(default=None, min_length=1, max_length=50),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    # Додаткова перевірка: чи це точно адмін?
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users, total = crud.get_all_users(db, search, page, page_size)
    return schemas.ExpertListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )

# Бізнес-ендпоінт - тільки для гемологів (експертів)
# Повертає список всіх активних гемологів
# Доступ лише з валідним токеном
@app.get("/experts/", response_model=List[schemas.ExpertBase])
def read_experts(
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user) # Перевірка токена
):
    experts = crud.get_active_experts(db)
    return experts

# Ендпоінт "Я" (профіль поточного юзера)
@app.get("/users/me", response_model=schemas.ExpertBase)
def read_user_me(current_user: models.Expert = Depends(get_current_user)):
    return current_user


@app.put("/users/me/profile", response_model=schemas.ExpertBase)
def update_my_profile(
    profile: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if profile.username and profile.username != current_user.username:
        existing_user = crud.get_user_by_username(db, profile.username)
        if existing_user is not None:
            raise HTTPException(status_code=400, detail="Username already registered")
    return crud.update_own_profile(db, current_user, profile)


@app.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_my_password(
    password_update: schemas.PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if not crud.update_own_password(db, current_user, password_update):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def require_report_access(report: models.DiamondReport, current_user: models.Expert) -> None:
    if current_user.role != "admin" and report.expert_id != current_user.expert_id:
        raise HTTPException(status_code=403, detail="You do not have access to this report")


def require_operational_report_access(
    report: models.DiamondReport,
    current_user: models.Expert,
    *,
    write: bool = False,
) -> None:
    """Keep demo records out of every ordinary report route.

    A gemologist receives an opaque response.  Administrators use a separate
    read-only dataset route; attempts to mutate a demo row remain explicit.
    """
    if report.record_scope != "operational":
        if current_user.role != "admin" or not write:
            raise HTTPException(status_code=404, detail="Report not found")
        raise HTTPException(status_code=409, detail="Demo reports are read-only")
    require_report_access(report, current_user)


def require_admin(current_user: models.Expert) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")


def require_demo_admin(current_user: models.Expert) -> None:
    """Do not reveal the existence of the isolated demo surface to experts."""
    if current_user.role != "admin":
        raise HTTPException(status_code=404, detail="Demo dataset not found")


def _attach_system_market_reference_when_available(
    db: Session, *, report: models.DiamondReport, actor: models.Expert,
) -> None:
    """Best-effort enrichment that never prevents a report save.

    A missing policy/snapshot, unsupported stone or temporarily unavailable FX
    endpoint leaves the report valid but without a new automatic reference.
    """
    policy = crud.get_market_reference_policy(db)
    if policy is None:
        return
    provider_codes = crud.get_enabled_market_reference_provider_codes(db, policy_id=policy.policy_id)
    if not provider_codes:
        return
    fx_snapshot = None
    if policy.use_fx_conversion:
        if policy.fx_provider_code != "nbu":
            return
        schedule = crud.get_market_provider_schedule(db, policy.fx_provider_code)
        if schedule is None:
            # Compatibility for databases that have not yet applied migration 0013.
            # Once a schedule exists, its block threshold is authoritative.
            fx_snapshot = next(iter(crud.get_fx_data_snapshots(db)), None)
        else:
            fx_snapshot = crud.get_latest_fresh_fx_snapshot(
                db, provider_code=policy.fx_provider_code,
                max_age_hours=schedule.block_after_hours, now=datetime.now(timezone.utc),
            )
        if fx_snapshot is None:
            return
    for provider_code in provider_codes:
        candidate = crud.prepare_system_market_reference(db, report=report, provider_code=provider_code)
        if candidate is None or crud.system_market_reference_exists(db, report=report, candidate=candidate):
            continue
        crud.attach_system_market_reference(
            db, report=report, candidate=candidate, actor=actor, fx_snapshot=fx_snapshot,
        )


def ensure_active_admin_remains(
    db: Session, target: models.Expert, target_role: str, target_active: bool,
) -> None:
    """Keep at least one active administrator able to operate the system."""
    removes_active_admin = target.is_active and target.role == "admin" and (
        not target_active or target_role != "admin"
    )
    if not removes_active_admin:
        return
    active_admins = db.query(models.Expert).filter(
        models.Expert.role == "admin", models.Expert.is_active.is_(True)
    ).count()
    if active_admins <= 1:
        raise HTTPException(status_code=409, detail="The last active administrator cannot be deactivated or demoted")


def to_public_passport_view(
    db: Session,
    passport: models.PublicPassport,
    report: models.DiamondReport,
    stone: models.Stone,
) -> schemas.PublicPassportView:
    """Build the explicit anonymous allow-list without exposing private ORM data."""
    return schemas.PublicPassportView(
        public_id=passport.public_id,
        report_id=report.report_id,
        issued_at=report.issued_at,
        public_updated_at=crud.get_public_projection_updated_at(db, passport),
        examination_date=report.examination_date,
        shape=stone.shape,
        carat_weight=stone.carat_weight,
        color_grade=stone.color_grade,
        clarity_grade=stone.clarity_grade,
        measurements_length=stone.measurements_length,
        measurements_width=stone.measurements_width,
        measurements_depth=stone.measurements_depth,
        system_proportions_grade=report.system_proportions_grade,
        system_cut_grade=report.system_cut_grade,
        expert_proportions_grade=report.expert_proportions_grade,
        expert_cut_grade=report.expert_cut_grade,
        origin=stone.origin,
        treatment_status=stone.treatment_status,
        identification_status=stone.identification_status,
    )


def validate_passport_url(public_url: str, public_id: str) -> None:
    """Permit QR content only for the current public passport URL."""
    parsed = urlparse(public_url)
    is_valid = (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
        and parsed.path.endswith("/passport.html")
        and parse_qs(parsed.query).get("id") == [public_id]
    )
    if not is_valid:
        raise HTTPException(status_code=422, detail="Invalid public passport URL")


@app.get("/public/passports/{public_id}", response_model=schemas.PublicPassportView)
def read_public_passport(
    public_id: str,
    db: Session = Depends(get_db),
):
    result = crud.get_public_passport_view(db, public_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Passport not found")
    passport, report, stone = result
    return to_public_passport_view(db, passport, report, stone)


def get_public_passport_report_or_404(db: Session, public_id: str) -> models.DiamondReport:
    """Resolve a valid public token without disclosing why an unavailable token failed."""
    result = crud.get_public_passport_view(db, public_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Passport not found")
    _passport, report, _stone = result
    return report


@app.get("/public/passports/{public_id}/media", response_model=List[schemas.PublicPassportMediaAsset])
def read_public_passport_media(public_id: str, db: Session = Depends(get_db)):
    report = get_public_passport_report_or_404(db, public_id)
    return crud.get_public_media_assets(db, report.report_id)


@app.get("/public/passports/{public_id}/media/{media_id}/content")
def read_public_passport_media_content(
    public_id: str,
    media_id: int,
    db: Session = Depends(get_db),
):
    report = get_public_passport_report_or_404(db, public_id)
    asset = crud.get_public_media_asset(db, report.report_id, media_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Public passport media not found")
    path = media_storage.get_storage_path(asset.storage_key)
    if not path.is_file() or not media_storage.has_expected_digest(path, asset.sha256):
        raise HTTPException(status_code=404, detail="Public passport media not found")
    return FileResponse(
        path,
        media_type=asset.mime_type,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/reports", response_model=schemas.ReportListResponse)
def read_report_domain_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    report_status: Optional[schemas.ReportStatus] = None,
    market_status: Optional[schemas.MarketStatus] = None,
    sold: Optional[bool] = None,
    shape: Optional[str] = Query(default=None, min_length=1, max_length=50),
    color_grade: Optional[int] = Query(default=None, ge=0, le=99),
    clarity_grade: Optional[int] = Query(default=None, ge=0, le=99),
    cut_grade: Optional[int] = Query(default=None, ge=0, le=99),
    carat_min: Optional[Decimal] = Query(default=None, ge=0),
    carat_max: Optional[Decimal] = Query(default=None, ge=0),
    price_min: Optional[Decimal] = Query(default=None, ge=0),
    price_max: Optional[Decimal] = Query(default=None, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    expert_id: Optional[int] = Query(default=None, ge=1),
    search: Optional[str] = Query(default=None, min_length=1, max_length=20),
    sort: schemas.ReportListSort = "report_date_desc",
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    reports, total = crud.get_report_domain_list(
        db,
        current_user=current_user,
        status=report_status,
        market_status=market_status,
        sold=sold,
        shape=shape,
        color_grade=color_grade,
        clarity_grade=clarity_grade,
        cut_grade=cut_grade,
        carat_min=carat_min,
        carat_max=carat_max,
        price_min=price_min,
        price_max=price_max,
        date_from=date_from,
        date_to=date_to,
        expert_id=expert_id,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return schemas.ReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@app.get("/demo/datasets/{dataset_id}", response_model=schemas.DemoDatasetResponse)
def read_demo_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Read one immutable synthetic-data manifest through an explicit admin route."""
    require_demo_admin(current_user)
    dataset = crud.get_demo_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Demo dataset not found")
    try:
        return crud.get_demo_dataset_response(dataset)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/demo/datasets/{dataset_id}/reports", response_model=schemas.ReportListResponse)
def read_demo_dataset_reports(
    dataset_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    report_status: Optional[schemas.ReportStatus] = None,
    market_status: Optional[schemas.MarketStatus] = None,
    shape: Optional[str] = Query(default=None, min_length=1, max_length=50),
    color_grade: Optional[int] = Query(default=None, ge=0, le=99),
    clarity_grade: Optional[int] = Query(default=None, ge=0, le=99),
    cut_grade: Optional[int] = Query(default=None, ge=0, le=99),
    carat_min: Optional[Decimal] = Query(default=None, ge=0),
    carat_max: Optional[Decimal] = Query(default=None, ge=0),
    price_min: Optional[Decimal] = Query(default=None, ge=0),
    price_max: Optional[Decimal] = Query(default=None, ge=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = Query(default=None, min_length=1, max_length=50),
    sort: schemas.ReportListSort = "report_id_desc",
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """List exactly one dataset, never a mixed operational/demo population."""
    require_demo_admin(current_user)
    if crud.get_demo_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Demo dataset not found")
    reports, total = crud.get_demo_report_domain_list(
        db, dataset_id=dataset_id, page=page, page_size=page_size,
        status=report_status, market_status=market_status, shape=shape,
        color_grade=color_grade, clarity_grade=clarity_grade, cut_grade=cut_grade,
        carat_min=carat_min, carat_max=carat_max, price_min=price_min,
        price_max=price_max, date_from=date_from, date_to=date_to, search=search, sort=sort,
    )
    return schemas.ReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@app.get("/demo/datasets/{dataset_id}/reports/{report_id}", response_model=schemas.ReportResponse)
def read_demo_dataset_report(
    dataset_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Read a demo report only in its manifest-bound, admin-only route."""
    require_demo_admin(current_user)
    if crud.get_demo_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Demo dataset not found")
    report = crud.get_demo_report_domain(db, dataset_id=dataset_id, report_id=report_id)
    if report is None or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Demo report not found")
    return report


@app.get("/demo/datasets/{dataset_id}/reports/{report_id}/passport-preview/pdf", response_class=Response)
def download_demo_report_passport_preview_pdf(
    dataset_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Download an admin-only synthetic preview; it never creates public state."""
    require_demo_admin(current_user)
    if crud.get_demo_dataset(db, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Demo dataset not found")
    report = crud.get_demo_report_domain(db, dataset_id=dataset_id, report_id=report_id)
    if report is None or report.stone is None:
        raise HTTPException(status_code=404, detail="Demo report not found")
    grade_labels = {(mapping.category, mapping.grade_value): mapping.grade_label for mapping in crud.get_mappings(db)}
    document = build_demo_passport_preview_pdf(report, report.stone, grade_labels)
    return Response(
        content=document,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="demo-preview-{report_id}.pdf"'},
    )


@app.post("/reports", response_model=schemas.ReportResponse)
def create_report_domain(
    payload: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if current_user.role != "gemologist":
        raise HTTPException(status_code=403, detail="Only gemologists can create primary reports")
    report = crud.create_report_domain(db, payload=payload, author=current_user)
    _attach_system_market_reference_when_available(db, report=report, actor=current_user)
    return report


@app.post("/report-wizard-sessions", response_model=schemas.WizardWorkSessionState)
def start_report_wizard_session(
    payload: schemas.WizardWorkSessionStart,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    try:
        session = crud.start_wizard_work_session(db, actor=current_user, signal=payload)
        db.commit()
        return session
    except crud.ReportDomainError as error:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Wizard session is no longer active") from error


@app.get("/reports/next-id", response_model=schemas.ReportIdPreview)
def preview_next_report_id(
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if current_user.role != "gemologist":
        raise HTTPException(status_code=403, detail="Only gemologists can create primary reports")
    return schemas.ReportIdPreview(report_id=crud._next_report_id(db))


@app.post("/reports/preview", response_model=schemas.ReportCalculationPreview)
def preview_report_calculation(
    stone: schemas.ReportCalculationInput,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if current_user.role != "gemologist":
        raise HTTPException(status_code=403, detail="Only gemologists can create primary reports")
    return crud.preview_report_calculation(db, stone)


@app.get("/reports/{report_id}", response_model=schemas.ReportResponse)
def read_report_domain(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user)
    return report


@app.get("/reports/{report_id}/valuations", response_model=List[schemas.StoneValuationResponse])
def read_report_valuations(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user)
    return crud.get_report_valuations(db, report)


@app.post("/reports/{report_id}/valuations/market-reference", response_model=schemas.StoneValuationResponse)
def attach_report_market_reference(
    report_id: str,
    payload: schemas.MarketReferenceAttachRequest,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    snapshot = crud.get_market_data_snapshot(db, payload.snapshot_id)
    if snapshot is None or snapshot.status != "approved":
        raise HTTPException(status_code=422, detail="Select an approved market-data snapshot")
    if snapshot.snapshot_kind != "market_reference":
        raise HTTPException(status_code=422, detail="This snapshot cannot create a market reference")
    policy = crud.get_market_reference_policy(db)
    if policy is None or snapshot.provider_code not in crud.get_enabled_market_reference_provider_codes(db):
        raise HTTPException(status_code=422, detail="Selected snapshot is not enabled by the current market-reference policy")
    try:
        fx_snapshot = None
        if policy.use_fx_conversion:
            if policy.fx_provider_code != "nbu":
                raise HTTPException(status_code=422, detail="Configured FX provider is not supported")
            schedule = crud.get_market_provider_schedule(db, policy.fx_provider_code)
            if schedule is None:
                # Compatibility for a pre-0013 database; migration 0013 makes
                # freshness blocking mandatory through the configured schedule.
                fx_snapshot = next(iter(crud.get_fx_data_snapshots(db)), None)
            else:
                fx_snapshot = crud.get_latest_fresh_fx_snapshot(
                    db, provider_code=policy.fx_provider_code,
                    max_age_hours=schedule.block_after_hours, now=datetime.now(timezone.utc),
                )
            if fx_snapshot is None:
                raise HTTPException(status_code=422, detail="Current FX snapshot is missing or stale; refresh NBU first")
        return crud.attach_market_reference(
            db, report=report, request=payload, actor=current_user, fx_snapshot=fx_snapshot,
        )
    except FxProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/reports/{report_id}/passport", response_model=schemas.ReportPassportPublicationStatus)
def read_report_publication(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user)
    passport = crud.get_active_public_passport(db, report_id)
    return schemas.ReportPassportPublicationStatus(passport=passport)


@app.post("/reports/{report_id}/passport", response_model=schemas.PublicPassportResponse)
def publish_report_passport(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    try:
        return crud.publish_public_passport(db, report=report, actor=current_user)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/reports/{report_id}/passport/reissue", response_model=schemas.PublicPassportResponse)
def reissue_report_passport(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    try:
        return crud.publish_public_passport(db, report=report, actor=current_user, reissue=True)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/reports/{report_id}/passport/qr", response_class=Response)
def read_report_passport_qr(
    report_id: str,
    public_url: str = Query(min_length=1, max_length=2_048),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    passport = crud.get_active_public_passport(db, report_id)
    if passport is None:
        raise HTTPException(status_code=404, detail="Public passport not found")
    validate_passport_url(public_url, passport.public_id)
    image = qrcode.make(public_url, image_factory=SvgPathImage)
    return Response(content=image.to_string(), media_type="image/svg+xml")


@app.get("/reports/{report_id}/passport/pdf", response_class=Response)
def download_report_passport_pdf(
    report_id: str,
    public_url: str = Query(min_length=1, max_length=2_048),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Download an on-demand PDF from the same allow-listed public projection."""
    require_admin(current_user)
    passport = crud.get_active_public_passport(db, report_id)
    if passport is None:
        raise HTTPException(status_code=404, detail="Public passport not found")
    validate_passport_url(public_url, passport.public_id)
    result = crud.get_public_passport_view(db, passport.public_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Public passport not found")
    public_passport, report, stone = result
    grade_labels = {
        (mapping.category, mapping.grade_value): mapping.grade_label
        for mapping in crud.get_mappings(db)
    }
    public_media: list[PublicPassportPdfMedia] = []
    for asset in crud.get_public_media_assets(db, report.report_id):
        path = media_storage.get_storage_path(asset.storage_key)
        if path.is_file() and media_storage.has_expected_digest(path, asset.sha256):
            public_media.append(PublicPassportPdfMedia(asset_type=asset.asset_type, content=path.read_bytes()))
    document = build_public_passport_pdf(
        to_public_passport_view(db, public_passport, report, stone),
        public_url,
        grade_labels,
        public_media,
    )
    return Response(
        content=document,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="passport-{report_id}.pdf"'},
    )


@app.delete("/reports/{report_id}/passport", status_code=status.HTTP_204_NO_CONTENT)
def revoke_report_passport(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    if not crud.revoke_public_passport(db, report=report, actor=current_user):
        raise HTTPException(status_code=404, detail="Public passport not found")


@app.put("/reports/{report_id}", response_model=schemas.ReportResponse)
def update_report_domain(
    report_id: str,
    payload: schemas.ReportUpdate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    try:
        updated_report = crud.update_report_domain(
            db,
            report=report,
            payload=payload,
            actor=current_user,
        )
        _attach_system_market_reference_when_available(db, report=updated_report, actor=current_user)
        return updated_report
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/reports/{report_id}/transitions", response_model=schemas.ReportResponse)
def transition_report_domain(
    report_id: str,
    payload: schemas.ReportTransition,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    try:
        return crud.transition_report_domain(
            db,
            report=report,
            target_status=payload.target_status,
            actor=current_user,
            reason=payload.reason,
        )
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/reports/{report_id}/events", response_model=List[schemas.ReportEventResponse])
def read_report_domain_events(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user)
    return crud.get_report_events(db, report_id)


def get_report_for_media(
    db: Session,
    report_id: str,
    current_user: models.Expert,
    *,
    write: bool = False,
) -> models.DiamondReport:
    """Authorize an existing private report for media access."""
    report = crud.get_report_domain(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=write)
    return report


@app.get("/reports/{report_id}/media", response_model=List[schemas.MediaAssetResponse])
def read_report_media(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    get_report_for_media(db, report_id, current_user)
    return crud.get_media_assets(db, report_id)


@app.post("/reports/{report_id}/media", response_model=schemas.MediaAssetResponse)
async def upload_report_media(
    report_id: str,
    asset_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = get_report_for_media(db, report_id, current_user, write=True)
    if report.status != "draft":
        raise HTTPException(status_code=422, detail="Only draft reports can receive media assets")
    try:
        storage_data = media_storage.store_upload(
            report_id=report_id,
            asset_type=asset_type,
            upload=file,
        )
        try:
            return crud.create_media_asset(
                db,
                report_id=report_id,
                uploaded_by_id=current_user.expert_id,
                asset_type=asset_type,
                storage_data=storage_data,
            )
        except Exception:
            media_storage.remove_stored_file(str(storage_data["storage_key"]))
            raise
    finally:
        await file.close()


@app.get("/reports/{report_id}/media/{media_id}/content")
def read_report_media_content(
    report_id: str,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    get_report_for_media(db, report_id, current_user)
    asset = crud.get_media_asset(db, report_id, media_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    path = media_storage.get_storage_path(asset.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(path, media_type=asset.mime_type, filename=asset.original_filename)


@app.put("/reports/{report_id}/media/{media_id}/publication", response_model=schemas.MediaAssetResponse)
def update_report_media_publication(
    report_id: str,
    media_id: int,
    payload: schemas.MediaPublicationUpdate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    asset = crud.get_media_asset(db, report_id, media_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    try:
        return crud.set_media_asset_publication(
            db, report=report, media_asset=asset, is_public=payload.is_public, actor=current_user,
        )
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.delete("/reports/{report_id}/media/{media_id}")
def delete_report_media(
    report_id: str,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = get_report_for_media(db, report_id, current_user, write=True)
    if report.status != "draft":
        raise HTTPException(status_code=422, detail="Only draft reports can remove media assets")
    asset = crud.get_media_asset(db, report_id, media_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    crud.delete_media_asset(db, asset)
    media_storage.remove_stored_file(asset.storage_key)
    return {"message": "Media asset deleted"}


@app.get("/reference-values", response_model=List[schemas.ReferenceValueResponse])
def read_reference_values(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    return crud.get_reference_values(db, category)

# Створення юзера (тільки для адміна)
@app.post("/users/", response_model=schemas.ExpertBase)
def create_user(
    user_data: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    require_admin(current_user)
    
    # Перевірка чи юзер вже існує
    db_user = crud.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    return crud.create_user(db=db, user=user_data)

# Оновлення юзера (тільки для адміна)
@app.put("/users/{expert_id}", response_model=schemas.ExpertBase)
def update_user(
    expert_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    require_admin(current_user)
    target = crud.get_user_by_id(db, expert_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.username and user_data.username != target.username:
        existing_user = crud.get_user_by_username(db, user_data.username)
        if existing_user is not None:
            raise HTTPException(status_code=400, detail="Username already registered")
    ensure_active_admin_remains(db, target, user_data.role or target.role, target.is_active)
    return crud.update_user(db, expert_id, user_data)

# Видалення юзера (тільки для адміна)
@app.post("/users/{expert_id}/deactivate", response_model=schemas.ExpertBase)
def deactivate_user(
    expert_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    require_admin(current_user)
    target = crud.get_user_by_id(db, expert_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.expert_id == current_user.expert_id:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
    ensure_active_admin_remains(db, target, target.role, False)
    return crud.set_user_active(db, expert_id, False)


@app.post("/users/{expert_id}/activate", response_model=schemas.ExpertBase)
def activate_user(
    expert_id: int,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    activated = crud.set_user_active(db, expert_id, True)
    if activated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return activated

# Статистика експертів
@app.get("/statistics/expert-performance", response_model=List[schemas.ExpertStats])
def get_stats(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Admin-only operational snapshot; no pricing, ML, or personnel scoring."""
    require_admin(current_user)
    try:
        return crud.get_expert_stats(db, date_from=date_from, date_to=date_to)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/statistics/admin-review-performance", response_model=schemas.AdminReviewStatisticsResponse)
def get_admin_review_stats(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Admin-only review-cycle timing, distinct from active operator work time."""
    require_admin(current_user)
    try:
        return crud.get_admin_review_stats(db, date_from=date_from, date_to=date_to)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/reports/{report_id}/work-session", response_model=schemas.ReportWorkSessionState)
def record_report_work_session(
    report_id: str,
    payload: schemas.ReportWorkSessionSignal,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Record a server-timed active draft signal from its owning gemologist."""
    report = crud.get_report_domain(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_operational_report_access(report, current_user, write=True)
    try:
        result = crud.record_work_session_signal(db, report=report, actor=current_user, signal=payload)
        db.commit()
        return result
    except crud.ReportDomainError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A work session was opened in another tab") from error

@app.get("/market/mappings", response_model=List[schemas.GradeMappingSchema])
def read_mappings(category: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Публічний ендпоінт для отримання довідників (Grade Mappings).
    Використовується фронтендом для рендерингу форм.
    
    category: (опціонально) фільтр, наприклад 'color', 'cut'.
    """
    return crud.get_mappings(db, category)

# Отримати поточну ринкову ціну
@app.get("/market/price", response_model=schemas.MarketPriceResponse)
def read_current_price(db: Session = Depends(get_db)):
    price = crud.get_latest_market_price(db)
    if not price:
        raise HTTPException(status_code=404, detail="Market price not set")
    return price

# Встановити нову ціну (Тільки Адмін)
@app.post("/market/price", response_model=schemas.MarketPriceResponse)
def update_market_price(
    price_data: schemas.MarketPriceCreate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    # Перевірка прав
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update market prices")
    
    return crud.create_market_price(db, price_data, admin_id=current_user.expert_id)


@app.get("/market-data/providers", response_model=List[schemas.MarketDataProviderResponse])
def read_market_data_providers(
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    return crud.get_market_data_providers(db)


@app.get("/market-data/policy", response_model=schemas.MarketReferencePolicyResponse)
def read_market_reference_policy(
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    policy = crud.get_market_reference_policy(db)
    if policy is None:
        raise HTTPException(status_code=404, detail="Market-reference policy is not initialized")
    return crud.get_market_reference_policy_response(db, policy)


@app.put("/market-data/policy", response_model=schemas.MarketReferencePolicyResponse)
def update_market_reference_policy(
    payload: schemas.MarketReferencePolicyUpdate,
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    try:
        policy = crud.update_market_reference_policy(db, payload=payload, actor=current_user)
        return crud.get_market_reference_policy_response(db, policy)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/market-data/snapshots", response_model=List[schemas.MarketDataSnapshotResponse])
def read_market_data_snapshots(
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    return crud.get_market_data_snapshots(db)


@app.get("/market-data/fx-snapshots", response_model=List[schemas.FxDataSnapshotResponse])
def read_fx_data_snapshots(
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    return crud.get_fx_data_snapshots(db)


@app.get("/market-data/provider-schedules", response_model=List[schemas.MarketProviderScheduleResponse])
def read_market_provider_schedules(
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    now = datetime.now(timezone.utc)
    responses = []
    for schedule in crud.get_market_provider_schedules(db):
        latest = crud.latest_provider_retrieved_at(db, schedule.provider_code)
        responses.append(schemas.MarketProviderScheduleResponse(
            **{
                "provider_code": schedule.provider_code,
                "enabled": schedule.enabled,
                "timezone_name": schedule.timezone_name,
                "scheduled_hour": schedule.scheduled_hour,
                "scheduled_minute": schedule.scheduled_minute,
                "warn_after_hours": schedule.warn_after_hours,
                "block_after_hours": schedule.block_after_hours,
                "updated_by_id": schedule.updated_by_id,
                "updated_at": schedule.updated_at,
                "freshness_status": freshness_status(
                    latest_retrieved_at=latest, warn_after_hours=schedule.warn_after_hours,
                    block_after_hours=schedule.block_after_hours, now=now,
                ),
                "latest_retrieved_at": latest,
            }
        ))
    return responses


@app.put("/market-data/provider-schedules/{provider_code}", response_model=schemas.MarketProviderScheduleResponse)
def update_market_provider_schedule(
    provider_code: str,
    payload: schemas.MarketProviderScheduleUpdate,
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    if payload.provider_code != provider_code:
        raise HTTPException(status_code=422, detail="Provider code must match the URL")
    try:
        schedule = crud.update_market_provider_schedule(db, payload=payload, actor=current_user)
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    latest = crud.latest_provider_retrieved_at(db, schedule.provider_code)
    return schemas.MarketProviderScheduleResponse(
        provider_code=schedule.provider_code, enabled=schedule.enabled, timezone_name=schedule.timezone_name,
        scheduled_hour=schedule.scheduled_hour, scheduled_minute=schedule.scheduled_minute,
        warn_after_hours=schedule.warn_after_hours, block_after_hours=schedule.block_after_hours,
        updated_by_id=schedule.updated_by_id, updated_at=schedule.updated_at,
        freshness_status=freshness_status(
            latest_retrieved_at=latest, warn_after_hours=schedule.warn_after_hours,
            block_after_hours=schedule.block_after_hours, now=datetime.now(timezone.utc),
        ), latest_retrieved_at=latest,
    )


@app.get("/market-data/operations", response_model=List[schemas.MarketProviderOperationResponse])
def read_market_provider_operations(
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    return crud.get_market_provider_operations(db)


@app.post("/market-data/providers/nbu/refresh", response_model=schemas.FxDataSnapshotResponse)
def refresh_nbu_fx_rate(
    db: Session = Depends(get_db), current_user: models.Expert = Depends(get_current_user),
):
    """Store a new immutable official USD/UAH response; reports are unchanged."""
    require_admin(current_user)
    operation = run_provider_operation(
        db, provider_code="nbu", trigger_type="manual", actor=current_user,
        fx_fetcher=fetch_nbu_usd_uah,
    )
    if operation.status == "failed":
        raise HTTPException(status_code=502, detail=operation.message or "NBU refresh failed")
    return db.get(models.FxDataSnapshot, operation.fx_snapshot_id)


@app.post("/market-data/providers/{provider_code}/fetch", response_model=schemas.MarketDataSnapshotResponse)
def fetch_market_data_candidate(
    provider_code: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Fetch external data, then persist it once as an immutable candidate."""
    require_admin(current_user)
    operation = run_provider_operation(
        db, provider_code=provider_code, trigger_type="manual", actor=current_user,
        market_provider_factory=get_market_provider,
    )
    if operation.status == "failed":
        raise HTTPException(status_code=502, detail=operation.message or "Market provider fetch failed")
    return db.get(models.MarketDataSnapshot, operation.market_snapshot_id)


@app.post("/market-data/snapshots/{snapshot_id}/approve", response_model=schemas.MarketDataSnapshotResponse)
def approve_market_data_snapshot(
    snapshot_id: int,
    payload: schemas.MarketSnapshotDecision,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    snapshot = crud.get_market_data_snapshot(db, snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Market-data snapshot not found")
    try:
        decided = crud.decide_market_data_snapshot(
            db, snapshot=snapshot, approve=True, actor=current_user, reason=payload.reason,
        )
        policy = crud.get_market_reference_policy(db)
        if policy and policy.use_fx_conversion and policy.fx_provider_code == "nbu":
            started_at = datetime.now(timezone.utc)
            try:
                fetched = fetch_nbu_usd_uah()
                fx_snapshot = crud.create_nbu_fx_snapshot(db, fetched=fetched, actor=current_user, commit=True)
                crud.create_market_provider_operation(
                    db, provider_code="nbu", trigger_type="manual", status="success", attempt_number=1,
                    started_at=started_at, completed_at=datetime.now(timezone.utc),
                    fx_snapshot_id=fx_snapshot.fx_snapshot_id,
                    message="Курс НБУ оновлено під час ручного затвердження market snapshot-а.", actor=current_user,
                )
            except FxProviderError as error:
                crud.create_market_provider_operation(
                    db, provider_code="nbu", trigger_type="manual", status="failed", attempt_number=1,
                    started_at=started_at, completed_at=datetime.now(timezone.utc), message=str(error), actor=current_user,
                )
        return decided
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/market-data/snapshots/{snapshot_id}/reject", response_model=schemas.MarketDataSnapshotResponse)
def reject_market_data_snapshot(
    snapshot_id: int,
    payload: schemas.MarketSnapshotDecision,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    snapshot = crud.get_market_data_snapshot(db, snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Market-data snapshot not found")
    try:
        return crud.decide_market_data_snapshot(
            db, snapshot=snapshot, approve=False, actor=current_user, reason=payload.reason,
        )
    except crud.ReportDomainError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
