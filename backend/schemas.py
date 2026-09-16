from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Optional
from datetime import date, datetime
from decimal import Decimal

# Схема для створення юзера (з паролем)
UserRole = Literal["admin", "gemologist"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    role: UserRole = "gemologist"

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

# Схема для оновлення юзера (пароль необов'язковий)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    role: Optional[UserRole] = None


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)


class PasswordUpdate(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("current_password", "new_password")
    @classmethod
    def password_must_fit_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

# Схема для експерта (дані, що ми віддаємо на фронт)
class ExpertBase(BaseModel):
    expert_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# Схема для статистики (для аналізу експертів)
class ExpertStats(BaseModel):
    expert_username: str
    total_reports: int
    avg_carat: float

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


# Report-domain contract used by the current private API.
ReportStatus = Literal["draft", "review", "issued", "void"]
Origin = Literal["unknown", "natural", "lab_grown", "other"]
TreatmentStatus = Literal["not_assessed", "none_detected", "disclosed", "confirmed"]
IdentificationStatus = Literal["preliminary", "confirmed", "inconclusive"]
MarketStatus = Literal["not_for_sale", "available", "reserved", "sold", "withdrawn"]
ReportListSort = Literal[
    "report_date_desc", "report_date_asc",
    "report_id_asc", "report_id_desc",
    "shape_asc", "shape_desc",
    "carat_desc", "carat_asc",
    "color_asc", "color_desc",
    "clarity_asc", "clarity_desc",
    "cut_asc", "cut_desc",
    "price_desc", "price_asc",
    "report_status_asc", "report_status_desc",
    "market_status_asc", "market_status_desc",
]


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
    examination_date: date
    expert_comment: Optional[str] = None
    expert_proportions_grade: Optional[int] = Field(default=None, ge=0, le=99)
    expert_cut_grade: Optional[int] = Field(default=None, ge=0, le=99)


class ReportUpdate(BaseModel):
    stone: StoneDraft
    examination_date: date
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
    examination_date: Optional[date]
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
    price: Optional[Decimal]
    stone: StoneResponse


class ReportListResponse(BaseModel):
    """Server-paginated, access-scoped report list for the dashboard."""

    items: list[ReportResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportIdPreview(BaseModel):
    """A non-reserving preview; POST /reports remains authoritative."""

    report_id: str


class ReportCalculationPreview(BaseModel):
    system_proportions_grade: int
    system_cut_grade: int
    calculation_rule_version: str
    demo_price_usd: Optional[Decimal] = None


class ReportCalculationInput(BaseModel):
    """Only the values required for an unsaved IDC preview."""

    table_percent: float = Field(gt=0, le=100)
    depth_percent: float = Field(gt=0, le=100)
    crown_angle: float = Field(gt=0, le=90)
    pavilion_angle: float = Field(gt=0, le=90)
    polish_grade: int = Field(ge=0, le=99)
    symmetry_grade: int = Field(ge=0, le=99)
    carat_weight: Optional[Decimal] = Field(default=None, gt=0, le=100)
    color_grade: Optional[int] = Field(default=None, ge=0, le=99)
    clarity_grade: Optional[int] = Field(default=None, ge=0, le=99)


class ReferenceValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    code: str
    label: str
    sort_order: int


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


class PublicPassportResponse(BaseModel):
    """Private publication state returned only to an administrator."""

    model_config = ConfigDict(from_attributes=True)

    public_id: str
    report_id: str
    is_active: bool
    created_at: datetime
    revoked_at: Optional[datetime]


class PublicPassportView(BaseModel):
    """Minimal anonymous projection; intentionally excludes private report data."""

    public_id: str
    report_id: str
    issued_at: datetime
    examination_date: Optional[date]
    shape: str
    carat_weight: Decimal
    color_grade: int
    clarity_grade: int
    measurements_length: Optional[Decimal]
    measurements_width: Optional[Decimal]
    measurements_depth: Optional[Decimal]
    system_proportions_grade: Optional[int]
    system_cut_grade: Optional[int]
    expert_proportions_grade: Optional[int]
    expert_cut_grade: Optional[int]
    origin: Origin
    treatment_status: TreatmentStatus
    identification_status: IdentificationStatus
