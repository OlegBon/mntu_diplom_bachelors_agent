from sqlalchemy import Column, DateTime, Integer, String, DECIMAL, ForeignKey, Enum, TIMESTAMP, Boolean, UniqueConstraint, Text
from sqlalchemy.sql import func
from .database import Base

class Expert(Base):
    __tablename__ = "experts"
    __table_args__ = {"schema": "diamond_oltp"}

    expert_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    middle_name = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('admin', 'gemologist'), default='gemologist')
    created_at = Column(TIMESTAMP, server_default=func.now())

class DiamondReport(Base):
    __tablename__ = "diamond_reports"
    __table_args__ = {"schema": "diamond_oltp"}

    report_id = Column(String(20), primary_key=True, index=True)
    report_date = Column(DateTime, nullable=False)
    
    # --- Форма (Обов'язкове поле) ---
    shape = Column(String(50), nullable=False) 

    # --- Геометрія (3D) ---
    measurements_length = Column(DECIMAL(5, 2))
    measurements_width = Column(DECIMAL(5, 2))
    measurements_depth = Column(DECIMAL(5, 2))

    # --- Фізичні параметри (IDC) ---
    table_percent = Column(DECIMAL(5,2))
    depth_percent = Column(DECIMAL(5,2))
    crown_angle = Column(DECIMAL(5,2))
    pavilion_angle = Column(DECIMAL(5,2))
    
    # --- Деталі ---
    girdle_thickness = Column(String(50))
    culet_size = Column(String(50))

    # --- 4C ---
    carat_weight = Column(DECIMAL(10,2))
    color_grade = Column(Integer)
    clarity_grade = Column(Integer)
    cut_grade = Column(Integer)
    
    # --- Finish ---
    polish_grade = Column(Integer)
    symmetry_grade = Column(Integer)
    proportions_grade = Column(Integer)
    fluorescence_grade = Column(Integer)
    stone_origin = Column(Integer)
    
    # --- Метадані ---
    expert_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"))
    evaluation_time_sec = Column(Integer)
    
    # --- Аналітика ---
    expert_comment = Column(Text, nullable=True)
    report_notes_length = Column(Integer)
    report_sentiment = Column(Integer)
    
    plotting_image = Column(String(255), nullable=True)
    real_image = Column(String(255), nullable=True)
    
    # --- Ринок ---
    price = Column(DECIMAL(12,2))
    is_investment_grade = Column(Boolean, default=False)
    is_report_rejected = Column(Boolean, default=False)
    is_sold = Column(Boolean, default=False)
    days_on_market = Column(Integer, nullable=True)
    sale_date = Column(DateTime, nullable=True)

class GradeMapping(Base):
    __tablename__ = "grade_mappings"
    __table_args__ = (
        UniqueConstraint('category', 'grade_value', name='uix_category_grade'),
        {"schema": "diamond_market"}
    )

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    grade_value = Column(Integer, nullable=False)
    grade_label = Column(String(50), nullable=False)

class MarketPriceRef(Base):
    __tablename__ = "market_price_reference"
    __table_args__ = {"schema": "diamond_market"}

    id = Column(Integer, primary_key=True, index=True)
    price_index_value = Column(DECIMAL(10,4), nullable=False)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now())
    notes = Column(String(255), nullable=True)


class MlResult(Base):
    """Зарезервований результат майбутнього ML-потоку.

    Модель відповідає наявній MariaDB-таблиці. Запис і читання результатів
    не додаються до цього етапу: їхній API та доменний життєвий цикл будуть
    окремою задачею разом із версіонованими міграціями.
    """

    __tablename__ = "ml_results"
    __table_args__ = {"schema": "diamond_analytics"}

    report_id = Column(String(20), primary_key=True)
    predicted_price = Column(DECIMAL(15, 2), nullable=True)
    predicted_class = Column(String(50), nullable=True)
    cluster_label = Column(String(50), nullable=True)
    som_x = Column(Integer, nullable=True)
    som_y = Column(Integer, nullable=True)
    processed_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
