from fastapi import FastAPI, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from jose import JWTError, jwt
import qrcode
from qrcode.image.svg import SvgPathImage

from . import crud, database, media_storage, models, schemas, security
from .passport_pdf import build_public_passport_pdf

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


def require_admin(current_user: models.Expert) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")


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
    passport: models.PublicPassport,
    report: models.DiamondReport,
    stone: models.Stone,
) -> schemas.PublicPassportView:
    """Build the explicit anonymous allow-list without exposing private ORM data."""
    return schemas.PublicPassportView(
        public_id=passport.public_id,
        report_id=report.report_id,
        issued_at=report.issued_at,
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
    return to_public_passport_view(passport, report, stone)


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


@app.post("/reports", response_model=schemas.ReportResponse)
def create_report_domain(
    payload: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    if current_user.role != "gemologist":
        raise HTTPException(status_code=403, detail="Only gemologists can create primary reports")
    return crud.create_report_domain(db, payload=payload, author=current_user)


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
    require_report_access(report, current_user)
    return report


@app.get("/reports/{report_id}/passport", response_model=schemas.PublicPassportResponse)
def read_report_publication(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    require_admin(current_user)
    report = crud.get_report_domain(db, report_id)
    if not report or report.stone_id is None:
        raise HTTPException(status_code=404, detail="Report not found")
    passport = crud.get_active_public_passport(db, report_id)
    if passport is None:
        raise HTTPException(status_code=404, detail="Public passport not found")
    return passport


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
    document = build_public_passport_pdf(
        to_public_passport_view(public_passport, report, stone),
        public_url,
        grade_labels,
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
    require_report_access(report, current_user)
    try:
        return crud.update_report_domain(
            db,
            report=report,
            payload=payload,
            actor=current_user,
        )
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
    require_report_access(report, current_user)
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
    require_report_access(report, current_user)
    return crud.get_report_events(db, report_id)


def get_report_for_media(
    db: Session,
    report_id: str,
    current_user: models.Expert,
) -> models.DiamondReport:
    """Authorize an existing private report for media access."""
    report = crud.get_report_domain(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    require_report_access(report, current_user)
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
    report = get_report_for_media(db, report_id, current_user)
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


@app.delete("/reports/{report_id}/media/{media_id}")
def delete_report_media(
    report_id: str,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    report = get_report_for_media(db, report_id, current_user)
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
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Admin-only operational snapshot; no pricing, ML, or personnel scoring."""
    require_admin(current_user)
    return crud.get_expert_stats(db)


@app.get("/statistics/admin-review-performance", response_model=schemas.AdminReviewStatisticsResponse)
def get_admin_review_stats(
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user),
):
    """Admin-only review-cycle timing, distinct from active operator work time."""
    require_admin(current_user)
    return crud.get_admin_review_stats(db)

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
