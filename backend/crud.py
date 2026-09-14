from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import date
import random

from . import models, schemas
from .security import get_password_hash

from .calculator import DiamondCalculator
from .ml_service import MLService

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
