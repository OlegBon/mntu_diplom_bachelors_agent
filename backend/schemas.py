from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
from datetime import datetime

# Схема для створення юзера (з паролем)
class UserCreate(BaseModel):
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    role: Optional[str] = "gemologist"

# Схема для оновлення юзера (пароль необов'язковий)
class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None

# Схема для експерта (дані, що ми віддаємо на фронт)
class ExpertBase(BaseModel):
    expert_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    role: str

    class Config:
        from_attributes = True

# Схема для створення нового звіту (те, що вводить експерт)
class DiamondCreate(BaseModel):
    # --- Ідентифікація ---
    shape: str  # Обов'язкове
    stone_origin: int # 0=Natural, 1=Lab

    # --- 4C (Основні) ---
    carat_weight: float
    color_grade: int
    clarity_grade: int
    
    # --- Геометрія (Measurements) ---
    measurements_length: float
    measurements_width: float
    measurements_depth: float

    # --- Фізичні параметри (IDC Input) ---
    table_percent: float
    depth_percent: float
    crown_angle: float
    pavilion_angle: float
    
    # --- Деталі ---
    girdle_thickness: Optional[str] = "Medium"
    culet_size: Optional[str] = "None"

    # --- Finish ---
    polish_grade: int
    symmetry_grade: int
    fluorescence_grade: int

    # --- Extra ---
    expert_comment: Optional[str] = None # Коментар експерта
    
    # Поля, які ми або порахуємо, або візьмемо введені (необов'язкові)
    cut_grade: Optional[int] = None
    proportions_grade: Optional[int] = None
    
    # Ціна (якщо 0 - викличемо ML)
    price: Optional[float] = 0.0

# Схема для оновлення звіту (всі поля необов'язкові)
class DiamondUpdate(BaseModel):
    is_sold: Optional[bool] = None
    price: Optional[float] = None

# Схема для статистики (для аналізу експертів)
class ExpertStats(BaseModel):
    expert_username: str
    total_reports: int
    avg_carat: float

# Схема для діаманта (базові поля)
class DiamondReportSchema(BaseModel):
    report_id: str
    report_date: datetime
    shape: str
    carat_weight: float
    color_grade: int
    clarity_grade: int
    cut_grade: int
    price: float
    is_sold: bool

    class Config:
        from_attributes = True

# Схема для токена (JWT)
class Token(BaseModel):
    access_token: str
    token_type: str

class GradeMappingSchema(BaseModel):
    """
    Схема для передачі довідкових даних (метаданих) на клієнт.
    Використовується для заповнення Select-елементів у формах.
    """
    category: str      # Назва категорії (напр. 'color', 'cut')
    grade_value: int   # Числове значення в БД (напр. 2)
    grade_label: str   # Текстова назва для людини (напр. 'F')

    class Config:
        from_attributes = True

class MarketPriceCreate(BaseModel):
    """Схема для встановлення нової ринкової ціни (Admin input)"""
    price_index_value: float
    notes: Optional[str] = None

class MarketPriceResponse(BaseModel):
    """Схема для відображення поточної ціни"""
    id: int
    price_index_value: float
    updated_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True


# New report-domain contract. Legacy Diamond* schemas stay untouched until the
# dashboard and wizard move from /diamonds to /reports.
ReportStatus = Literal["draft", "review", "issued", "void"]
Origin = Literal["unknown", "natural", "lab_grown", "other"]
TreatmentStatus = Literal["not_assessed", "none_detected", "disclosed", "confirmed"]
IdentificationStatus = Literal["preliminary", "confirmed", "inconclusive"]
MarketStatus = Literal["not_for_sale", "available", "reserved", "sold", "withdrawn"]


class StoneDraft(BaseModel):
    shape: str = Field(min_length=1, max_length=50)
    carat_weight: float = Field(gt=0, le=100)
    color_grade: int = Field(ge=0, le=99)
    clarity_grade: int = Field(ge=0, le=99)
    measurements_length: float = Field(gt=0, le=999)
    measurements_width: float = Field(gt=0, le=999)
    measurements_depth: float = Field(gt=0, le=999)
    table_percent: float = Field(gt=0, le=100)
    depth_percent: float = Field(gt=0, le=100)
    crown_angle: float = Field(gt=0, le=90)
    pavilion_angle: float = Field(gt=0, le=90)
    girdle_thickness: Optional[str] = Field(default=None, max_length=50)
    culet_size: Optional[str] = Field(default=None, max_length=50)
    polish_grade: int = Field(ge=0, le=99)
    symmetry_grade: int = Field(ge=0, le=99)
    fluorescence_grade: int = Field(ge=0, le=99)
    origin: Origin = "unknown"
    treatment_status: TreatmentStatus = "not_assessed"
    identification_status: IdentificationStatus = "preliminary"
    identification_method: Optional[str] = Field(default=None, max_length=255)
    identification_conclusion: Optional[str] = None
    market_status: MarketStatus = "not_for_sale"


class ReportCreate(BaseModel):
    stone: StoneDraft
    expert_comment: Optional[str] = None
    expert_proportions_grade: Optional[int] = Field(default=None, ge=0, le=99)
    expert_cut_grade: Optional[int] = Field(default=None, ge=0, le=99)


class ReportUpdate(BaseModel):
    stone: StoneDraft
    expert_comment: Optional[str] = None
    expert_proportions_grade: Optional[int] = Field(default=None, ge=0, le=99)
    expert_cut_grade: Optional[int] = Field(default=None, ge=0, le=99)


class ReportTransition(BaseModel):
    target_status: ReportStatus
    reason: Optional[str] = Field(default=None, max_length=2_000)


class StoneResponse(StoneDraft):
    model_config = ConfigDict(from_attributes=True)
    stone_id: int
    legacy_origin_code: Optional[int] = None


class ReportEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: int
    action: str
    from_status: Optional[str]
    to_status: Optional[str]
    actor_id: Optional[int]
    reason: Optional[str]
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    report_id: str
    status: ReportStatus
    report_date: datetime
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    issued_at: Optional[datetime]
    expert_id: Optional[int]
    issued_by_id: Optional[int]
    expert_comment: Optional[str]
    system_proportions_grade: Optional[int]
    system_cut_grade: Optional[int]
    calculation_rule_version: Optional[str]
    expert_proportions_grade: Optional[int]
    expert_cut_grade: Optional[int]
    expert_confirmed_at: Optional[datetime]
    stone: StoneResponse


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    media_id: int
    report_id: str
    asset_type: str
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    uploaded_by_id: int
    created_at: datetime
    is_public: bool
