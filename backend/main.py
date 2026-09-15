from fastapi import FastAPI, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
from jose import JWTError, jwt

from . import crud, database, media_storage, models, schemas, security

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
    if user is None:
        raise credentials_exception
    return user

# Авторизація - отримання токена (логін)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Шукаємо користувача в базі
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # Перевіряємо чи юзер існує і чи правильний пароль
    if not user or not security.verify_password(form_data.password, user.password_hash):
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
@app.get("/users/", response_model=List[schemas.ExpertBase])
def read_users(
    db: Session = Depends(get_db), 
    current_user: models.Expert = Depends(get_current_user)
):
    # Додаткова перевірка: чи це точно адмін?
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users = crud.get_all_users(db)
    return users

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


def require_report_access(report: models.DiamondReport, current_user: models.Expert) -> None:
    if current_user.role != "admin" and report.expert_id != current_user.expert_id:
        raise HTTPException(status_code=403, detail="You do not have access to this report")


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
        return crud.update_report_domain(db, report=report, payload=payload)
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
    """Authorize an existing report, including a temporary legacy-compatible one."""
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
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
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
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update users")
    
    updated_user = crud.update_user(db, expert_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user

# Видалення юзера (тільки для адміна)
@app.delete("/users/{expert_id}")
def delete_user(
    expert_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    deleted = crud.delete_user(db, expert_id=expert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {expert_id} deleted successfully"}

# Пошук звіту
@app.get("/diamonds/{report_id}", response_model=schemas.DiamondReportSchema)
def read_diamond(report_id: str, db: Session = Depends(get_db)):
    diamond = crud.get_diamond_report(db, report_id=report_id)
    if not diamond:
        raise HTTPException(status_code=404, detail="Diamond report not found")
    return diamond

# Створення нового звіту (тільки для авторизованих експертів)
@app.post("/diamonds/", response_model=schemas.DiamondReportSchema)
def create_report(
    diamond_data: schemas.DiamondCreate, # Pydantic перевірить типи даних
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user) # Тільки авторизовані
):
    if current_user.role != "gemologist":
        raise HTTPException(status_code=403, detail="Only gemologists can create reports")

    # Тут пізніше ми додамо виклик ML:
    # ml_results = ml_service.predict_price(diamond_data)
    # diamond_data.price = ml_results.price
    
    return crud.create_diamond_report(db=db, diamond=diamond_data, expert_id=current_user.expert_id)

# Список усіх діамантів (з фільтрацією, сортуванням, пошуком)
@app.get("/diamonds/", response_model=List[schemas.DiamondReportSchema])
def read_reports(
    skip: int = 0, 
    limit: int = 50,
    status: Optional[str] = "all",
    sort_by: Optional[str] = "newest",
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    reports = crud.get_reports(
        db, 
        skip=skip, 
        limit=limit, 
        status=status, 
        sort_by=sort_by, 
        search=search
    )
    return reports

# Оновлення звіту (доступно авторизованим)
@app.put("/diamonds/{report_id}", response_model=schemas.DiamondReportSchema)
def update_report(
    report_id: str, 
    update_data: schemas.DiamondUpdate, 
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    report = crud.get_diamond_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Diamond report not found")
    if current_user.role != "admin" and report.expert_id != current_user.expert_id:
        raise HTTPException(status_code=403, detail="Only the report owner or an admin can update reports")
    return crud.update_diamond_report(db, report, update_data)

# Видалення звіту (тільки для адміна)
@app.delete("/diamonds/{report_id}")
def delete_report(
    report_id: str, 
    db: Session = Depends(get_db),
    current_user: models.Expert = Depends(get_current_user)
):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete reports")
    report = crud.get_diamond_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Diamond report not found")
    crud.delete_diamond_report(db, report)
    return {"message": "Report deleted"}

# Статистика експертів
@app.get("/statistics/expert-performance", response_model=List[schemas.ExpertStats])
def get_stats(db: Session = Depends(get_db)):
    return crud.get_expert_stats(db)

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
