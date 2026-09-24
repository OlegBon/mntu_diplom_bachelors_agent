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
    password: Optional[str] = Field(default=None, min_length=8, max_length=72)
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    role: Optional[UserRole] = None

    @field_validator("password")
    @classmethod
    def admin_password_must_fit_bcrypt(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
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
    model_config = ConfigDict(from_attributes=True)

    expert_id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    role: str
    is_active: bool

class ExpertListResponse(BaseModel):
    items: list[ExpertBase]
    total: int
    page: int
    page_size: int
    total_pages: int

# Read-only operational workload snapshot. It is not a staff-performance score.
class ExpertStats(BaseModel):
    expert_id: int
    expert_username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    is_active: bool
    total_reports: int
    draft_reports: int
    review_reports: int
    issued_reports: int
    void_reports: int
    completed_work_sessions: int = 0
    total_active_seconds: int = 0
    avg_active_seconds: Optional[int] = None
    median_active_seconds: Optional[int] = None
    completed_first_save_timings: int = 0
    total_time_to_first_save_seconds: int = 0
    avg_time_to_first_save_seconds: Optional[int] = None
    median_time_to_first_save_seconds: Optional[int] = None
    shortest_work_sessions: list["WorkSessionDurationRecord"] = Field(default_factory=list)
    longest_work_sessions: list["WorkSessionDurationRecord"] = Field(default_factory=list)


class WorkSessionDurationRecord(BaseModel):
    report_id: str
    duration_seconds: int
    finished_at: datetime


class ReportWorkSessionSignal(BaseModel):
    action: Literal["start", "resume", "heartbeat", "pause", "save"]
    tab_id: str = Field(min_length=16, max_length=64, pattern=r"^[A-Za-z0-9-]+$")


class ReportWorkSessionState(BaseModel):
    work_session_id: str
    active_seconds: int
    is_active: bool


class WizardWorkSessionStart(BaseModel):
    tab_id: str = Field(min_length=16, max_length=64, pattern=r"^[A-Za-z0-9-]+$")


class WizardWorkSessionState(BaseModel):
    wizard_session_id: str


class ReviewDurationRecord(BaseModel):
    report_id: str
    decision: Literal["draft", "issued", "void"]
    duration_seconds: int
    decided_at: datetime


class AdminReviewStats(BaseModel):
    admin_id: int
    admin_username: str
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    is_active: bool
    completed_reviews: int
    returned_to_draft: int
    issued_reports: int
    voided_reports: int
    avg_review_duration_seconds: Optional[int]
    median_review_duration_seconds: Optional[int]
    shortest_reviews: list[ReviewDurationRecord]
    longest_reviews: list[ReviewDurationRecord]


class AdminReviewStatisticsResponse(BaseModel):
    admins: list[AdminReviewStats]
    pending_review_count: int
    oldest_review_started_at: Optional[datetime]

# Схема для токена (JWT)
class Token(BaseModel):
    access_token: str
    token_type: str

class GradeMappingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """
    Схема для передачі довідкових даних (метаданих) на клієнт.
    Використовується для заповнення Select-елементів у формах.
    """
    category: str      # Назва категорії (напр. 'color', 'cut')
    grade_value: int   # Числове значення в БД (напр. 2)
    grade_label: str   # Текстова назва для людини (напр. 'F')

class MarketPriceCreate(BaseModel):
    """Схема для встановлення нової ринкової ціни (Admin input)"""
    price_index_value: float
    notes: Optional[str] = None

class MarketPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Схема для відображення поточної ціни"""
    id: int
    price_index_value: float
    updated_at: datetime
    notes: Optional[str]

MarketSnapshotStatus = Literal["candidate", "approved", "rejected"]


class MarketDataProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_code: str
    display_name: str
    provider_type: str
    documentation_url: str
    terms_url: str
    scope_note: str
    is_active: bool


class MarketReferencePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_id: int
    market_provider_code: Optional[str]
    use_fx_conversion: bool
    fx_provider_code: Optional[str]
    updated_by_id: Optional[int]
    updated_at: datetime


class MarketReferencePolicyUpdate(BaseModel):
    market_provider_code: Optional[str] = Field(default=None, max_length=32)
    use_fx_conversion: bool
    fx_provider_code: Optional[str] = Field(default=None, max_length=32)


class MarketDataSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: int
    provider_code: str
    snapshot_kind: str
    status: MarketSnapshotStatus
    currency_code: str
    unit: str
    source_url: str
    methodology_url: str
    coverage_note: str
    quote_count: int
    content_sha256: str
    retrieved_at: datetime
    created_by_id: Optional[int]
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    decision_reason: Optional[str]
    created_at: datetime


class MarketSnapshotDecision(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=2_000)


class MarketReferenceAttachRequest(BaseModel):
    snapshot_id: int = Field(gt=0)
    applicability_confirmed: Literal[True]
    applicability_note: str = Field(min_length=10, max_length=2_000)


class StoneValuationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    valuation_id: int
    stone_id: int
    valuation_kind: str
    amount: Decimal
    currency_code: str
    unit: str
    source_name: str
    source_reference: Optional[str]
    market_snapshot_id: Optional[int]
    applicability_note: Optional[str]
    fx_snapshot_id: Optional[int]
    fx_rate: Optional[Decimal]
    fx_rate_date: Optional[date]
    converted_amount: Optional[Decimal]
    converted_currency_code: Optional[str]
    observed_at: datetime
    created_by_id: Optional[int]
    created_at: datetime




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
    wizard_session_id: Optional[str] = Field(default=None, min_length=36, max_length=36, pattern=r"^[A-Fa-f0-9-]+$")


class ReportUpdate(BaseModel):
    stone: StoneDraft
    examination_date: date
    expert_comment: Optional[str] = None
    expert_proportions_grade: Optional[int] = Field(default=None, ge=0, le=99)


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


class MarketReferenceSummary(BaseModel):
    """The preferred market-reference projection for one report list row."""

    amount: Decimal
    currency_code: str
    valuation_kind: str
    source_name: str
    market_snapshot_id: Optional[int]
    observed_at: datetime
    converted_amount: Optional[Decimal]
    converted_currency_code: Optional[str]
    fx_snapshot_id: Optional[int]
    fx_rate: Optional[Decimal]
    fx_rate_date: Optional[date]


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
    first_save_started_at: Optional[datetime]
    time_to_first_save_seconds: Optional[int]
    price: Optional[Decimal]
    market_reference: Optional[MarketReferenceSummary] = None
    stone: StoneResponse


class FxDataSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fx_snapshot_id: int
    provider_code: str
    base_currency_code: str
    quote_currency_code: str
    rate: Decimal
    rate_date: date
    source_url: str
    retrieved_at: datetime
    created_by_id: Optional[int]
    created_at: datetime


class MarketProviderScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_code: str
    enabled: bool
    timezone_name: str
    scheduled_hour: int
    scheduled_minute: int
    warn_after_hours: int
    block_after_hours: int
    updated_by_id: Optional[int]
    updated_at: datetime
    freshness_status: Literal["fresh", "warning", "stale", "missing"]
    latest_retrieved_at: Optional[datetime]


class MarketProviderScheduleUpdate(BaseModel):
    provider_code: str = Field(min_length=1, max_length=32)
    enabled: bool
    scheduled_hour: int = Field(ge=0, le=23)
    scheduled_minute: int = Field(ge=0, le=59)
    warn_after_hours: int = Field(ge=1, le=24 * 90)
    block_after_hours: int = Field(ge=1, le=24 * 180)


class MarketProviderOperationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operation_id: int
    provider_code: str
    trigger_type: Literal["manual", "scheduled"]
    status: Literal["success", "no_change", "failed", "skipped"]
    attempt_number: int
    started_at: datetime
    completed_at: datetime
    market_snapshot_id: Optional[int]
    fx_snapshot_id: Optional[int]
    message: Optional[str]
    initiated_by_id: Optional[int]


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
    system_market_reference_usd: Optional[Decimal] = None
    market_reference_provider_code: Optional[str] = None
    market_reference_snapshot_id: Optional[int] = None


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
    shape: Optional[str] = Field(default=None, max_length=50)
    origin: Optional[Origin] = None


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


class MediaPublicationUpdate(BaseModel):
    """Explicit admin decision whether an eligible image appears in a public passport."""

    is_public: bool


class PublicPassportMediaAsset(BaseModel):
    """Anonymous allow-listed media metadata; private file metadata stays private."""

    media_id: int
    asset_type: Literal["stone_photo", "plotting_diagram"]
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]


class PublicPassportResponse(BaseModel):
    """Private publication state returned only to an administrator."""

    model_config = ConfigDict(from_attributes=True)

    public_id: str
    report_id: str
    is_active: bool
    created_at: datetime
    revoked_at: Optional[datetime]


class ReportPassportPublicationStatus(BaseModel):
    """Private admin view of whether a report currently has a public passport."""

    passport: Optional[PublicPassportResponse]


class PublicPassportView(BaseModel):
    """Minimal anonymous projection; intentionally excludes private report data."""

    public_id: str
    report_id: str
    issued_at: datetime
    public_updated_at: datetime
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
