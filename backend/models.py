from sqlalchemy import CheckConstraint, Column, Date, DateTime, Integer, String, DECIMAL, ForeignKey, Enum, TIMESTAMP, Boolean, Index, UniqueConstraint, Text
from sqlalchemy.orm import relationship
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
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(TIMESTAMP, server_default=func.now())

class DiamondReport(Base):
    __tablename__ = "diamond_reports"
    __table_args__ = (
        CheckConstraint("record_scope IN ('operational', 'demo')", name="ck_diamond_reports_record_scope"),
        CheckConstraint(
            "(record_scope = 'operational' AND demo_dataset_id IS NULL) OR "
            "(record_scope = 'demo' AND demo_dataset_id IS NOT NULL)",
            name="ck_diamond_reports_scope_dataset",
        ),
        Index("ix_diamond_reports_scope_report_id", "record_scope", "report_id"),
        Index("ix_diamond_reports_demo_dataset_id", "demo_dataset_id"),
        {"schema": "diamond_oltp"},
    )

    report_id = Column(String(20), primary_key=True, index=True)
    # Scope is authoritative.  ID prefixes are only a human-visible convention.
    record_scope = Column(String(16), nullable=False, default="operational", server_default="operational")
    demo_dataset_id = Column(
        String(64), ForeignKey("diamond_oltp.demo_datasets.dataset_id"), nullable=True,
    )
    report_date = Column(DateTime, nullable=False)
    # Factual date supplied by the expert; never infer it from creation time.
    examination_date = Column(Date, nullable=True)
    # Legacy projection fields remain for historical data; current code reads
    # the normalized Stone and lifecycle columns. Their data cleanup is separate.
    stone_id = Column(Integer, ForeignKey("diamond_oltp.stones.stone_id"), nullable=True, index=True)
    stone = relationship("Stone", foreign_keys=[stone_id])
    status = Column(String(16), nullable=False, default="draft", server_default="draft")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    issued_by_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=True)
    system_proportions_grade = Column(Integer, nullable=True)
    system_cut_grade = Column(Integer, nullable=True)
    # Immutable identifier of the ruleset used for this report. Historical
    # reports retain their original code rather than being recalculated.
    calculation_rule_version = Column(String(32), nullable=True, index=True)
    expert_proportions_grade = Column(Integer, nullable=True)
    expert_cut_grade = Column(Integer, nullable=True)
    expert_confirmed_at = Column(DateTime, nullable=True)
    first_save_started_at = Column(DateTime, nullable=True)
    time_to_first_save_seconds = Column(Integer, nullable=True)
    
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


class DemoDataset(Base):
    """Immutable manifest that authorizes one synthetic demonstration dataset."""

    __tablename__ = "demo_datasets"
    __table_args__ = {"schema": "diamond_oltp"}

    dataset_id = Column(String(64), primary_key=True)
    label = Column(String(120), nullable=False)
    version = Column(String(64), nullable=False)
    generator_version = Column(String(64), nullable=False)
    content_sha256 = Column(String(64), nullable=False)
    provenance = Column(Text, nullable=False)
    scope_note = Column(Text, nullable=False)
    # JSON list of server-recognized scenarios, for example ["synthetic_som"].
    analysis_eligibility = Column(Text, nullable=False)
    record_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Stone(Base):
    """Stable physical identity and commercial state of a diamond."""

    __tablename__ = "stones"
    __table_args__ = {"schema": "diamond_oltp"}

    stone_id = Column(Integer, primary_key=True, index=True)
    legacy_source_report_id = Column(String(20), unique=True, nullable=True)
    shape = Column(String(50), nullable=False)
    measurements_length = Column(DECIMAL(5, 2), nullable=True)
    measurements_width = Column(DECIMAL(5, 2), nullable=True)
    measurements_depth = Column(DECIMAL(5, 2), nullable=True)
    table_percent = Column(DECIMAL(5, 2), nullable=True)
    depth_percent = Column(DECIMAL(5, 2), nullable=True)
    crown_angle = Column(DECIMAL(5, 2), nullable=True)
    pavilion_angle = Column(DECIMAL(5, 2), nullable=True)
    girdle_thickness = Column(String(50), nullable=True)
    culet_size = Column(String(50), nullable=True)
    carat_weight = Column(DECIMAL(10, 2), nullable=True)
    color_grade = Column(Integer, nullable=True)
    clarity_grade = Column(Integer, nullable=True)
    polish_grade = Column(Integer, nullable=True)
    symmetry_grade = Column(Integer, nullable=True)
    fluorescence_grade = Column(Integer, nullable=True)
    origin = Column(String(24), nullable=False, default="unknown", server_default="unknown")
    legacy_origin_code = Column(Integer, nullable=True)
    treatment_status = Column(String(24), nullable=False, default="not_assessed", server_default="not_assessed")
    identification_status = Column(String(24), nullable=False, default="preliminary", server_default="preliminary")
    identification_method = Column(String(255), nullable=True)
    identification_conclusion = Column(Text, nullable=True)
    market_status = Column(String(24), nullable=False, default="not_for_sale", server_default="not_for_sale")
    legacy_sale_date = Column(DateTime, nullable=True)
    legacy_days_on_market = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)


class ReportEvent(Base):
    """Append-only audit history for a report lifecycle action."""

    __tablename__ = "report_events"
    __table_args__ = {"schema": "diamond_oltp"}

    event_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(20), ForeignKey("diamond_oltp.diamond_reports.report_id"), nullable=False, index=True)
    action = Column(String(32), nullable=False)
    from_status = Column(String(16), nullable=True)
    to_status = Column(String(16), nullable=True)
    actor_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ReportWorkSession(Base):
    """A server-timed expert work session for one saved draft report."""

    __tablename__ = "report_work_sessions"
    __table_args__ = {"schema": "diamond_oltp"}

    work_session_id = Column(String(36), primary_key=True)
    report_id = Column(String(20), ForeignKey("diamond_oltp.diamond_reports.report_id"), nullable=False, index=True)
    expert_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=False, index=True)
    tab_id = Column(String(64), nullable=False)
    started_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True, index=True)
    active_seconds = Column(Integer, nullable=False, default=0, server_default="0")
    end_reason = Column(String(32), nullable=True)


class ReportWorkSessionEvent(Base):
    """Append-only evidence for server-timed draft work sessions."""

    __tablename__ = "report_work_session_events"
    __table_args__ = {"schema": "diamond_oltp"}

    work_session_event_id = Column(Integer, primary_key=True)
    work_session_id = Column(String(36), ForeignKey("diamond_oltp.report_work_sessions.work_session_id"), nullable=False, index=True)
    action = Column(String(16), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    active_seconds = Column(Integer, nullable=False)


class ReportWorkSessionLease(Base):
    """Mutable single-tab lease; append-only events remain the audit source."""

    __tablename__ = "report_work_session_leases"
    __table_args__ = {"schema": "diamond_oltp"}

    report_id = Column(String(20), ForeignKey("diamond_oltp.diamond_reports.report_id"), primary_key=True)
    expert_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), primary_key=True)
    work_session_id = Column(String(36), ForeignKey("diamond_oltp.report_work_sessions.work_session_id"), nullable=False, unique=True)
    tab_id = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class WizardWorkSession(Base):
    """Short-lived server timestamp for a new-report wizard before its first save."""

    __tablename__ = "wizard_work_sessions"
    __table_args__ = {"schema": "diamond_oltp"}

    wizard_session_id = Column(String(36), primary_key=True)
    expert_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=False, unique=True)
    tab_id = Column(String(64), nullable=False)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class MediaAsset(Base):
    """Private file metadata; the file body lives outside the database and Git."""

    __tablename__ = "media_assets"
    __table_args__ = {"schema": "diamond_oltp"}

    media_id = Column(Integer, primary_key=True, index=True)
    report_id = Column(
        String(20),
        ForeignKey("diamond_oltp.diamond_reports.report_id"),
        nullable=False,
        index=True,
    )
    asset_type = Column(String(32), nullable=False)
    storage_key = Column(String(255), nullable=False, unique=True)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    # Synthetic demo assets deliberately have no fictional or real operator.
    # Operational uploads still always set this field in the normal API flow.
    uploaded_by_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    is_public = Column(Boolean, nullable=False, default=False, server_default="0")


class PublicPassport(Base):
    """Revocable public projection token for an issued report."""

    __tablename__ = "public_passports"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_public_passports_public_id"),
        {"schema": "diamond_oltp"},
    )

    passport_id = Column(Integer, primary_key=True)
    report_id = Column(
        String(20),
        ForeignKey("diamond_oltp.diamond_reports.report_id"),
        nullable=False,
        index=True,
    )
    public_id = Column(String(64), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_by_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    revoked_at = Column(DateTime, nullable=True)


class GradingRuleset(Base):
    """Immutable metadata for a supported grading ruleset release."""

    __tablename__ = "grading_rulesets"
    __table_args__ = {"schema": "diamond_oltp"}

    ruleset_id = Column(String(32), primary_key=True)
    display_name = Column(String(100), nullable=False)
    source_title = Column(String(255), nullable=False)
    source_edition = Column(String(100), nullable=True)
    effective_from = Column(Date, nullable=True)
    algorithm_version = Column(String(32), nullable=False)
    scope_note = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class StoneValuation(Base):
    """A versioned, explicitly sourced amount; legacy report.price is excluded."""

    __tablename__ = "stone_valuations"
    __table_args__ = {"schema": "diamond_oltp"}

    valuation_id = Column(Integer, primary_key=True, index=True)
    stone_id = Column(Integer, ForeignKey("diamond_oltp.stones.stone_id"), nullable=False, index=True)
    valuation_kind = Column(String(32), nullable=False)
    amount = Column(DECIMAL(14, 2), nullable=False)
    currency_code = Column(String(3), nullable=False)
    unit = Column(String(24), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_reference = Column(String(255), nullable=True)
    # Cross-database FK is intentionally avoided for future PostgreSQL
    # portability; the domain service validates this market snapshot ID.
    market_snapshot_id = Column(Integer, nullable=True, index=True)
    applicability_note = Column(Text, nullable=True)
    # The FX rate is frozen with the valuation.  It is never recalculated from
    # a subsequently published NBU rate.
    fx_snapshot_id = Column(Integer, nullable=True, index=True)
    fx_rate = Column(DECIMAL(18, 8), nullable=True)
    fx_rate_date = Column(Date, nullable=True)
    converted_amount = Column(DECIMAL(14, 2), nullable=True)
    converted_currency_code = Column(String(3), nullable=True)
    observed_at = Column(DateTime, nullable=False)
    created_by_id = Column(Integer, ForeignKey("diamond_oltp.experts.expert_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class ReferenceValue(Base):
    """Text reference data used by the report-domain API and future admin UI."""

    __tablename__ = "reference_values"
    __table_args__ = (
        UniqueConstraint("category", "code", name="uix_reference_category_code"),
        {"schema": "diamond_market"},
    )

    reference_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    label = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

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


class MarketDataProvider(Base):
    """Registered source metadata; adding a provider does not alter reports."""

    __tablename__ = "market_data_providers"
    __table_args__ = {"schema": "diamond_market"}

    provider_code = Column(String(32), primary_key=True)
    display_name = Column(String(100), nullable=False)
    provider_type = Column(String(32), nullable=False)
    documentation_url = Column(String(255), nullable=False)
    terms_url = Column(String(255), nullable=False)
    scope_note = Column(Text, nullable=False)
    # Local vetted asset key only; never a remote provider-logo URL.
    brand_asset_key = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class MarketReferencePolicy(Base):
    """The mutable admin policy used only for future system references."""

    __tablename__ = "market_reference_policies"
    __table_args__ = {"schema": "diamond_market"}

    policy_id = Column(Integer, primary_key=True)
    market_provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=True,
    )
    use_fx_conversion = Column(Boolean, nullable=False, default=True, server_default="1")
    fx_provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=True,
    )
    updated_by_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class MarketReferencePolicyProvider(Base):
    """One enabled market-reference provider in the future-only policy."""

    __tablename__ = "market_reference_policy_providers"
    __table_args__ = (
        UniqueConstraint("policy_id", "provider_code", name="uq_market_policy_provider"),
        {"schema": "diamond_market"},
    )

    policy_provider_id = Column(Integer, primary_key=True)
    policy_id = Column(
        Integer, ForeignKey("diamond_market.market_reference_policies.policy_id"), nullable=False,
    )
    provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=False,
    )
    display_order = Column(Integer, nullable=False, default=0, server_default="0")
    updated_by_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class MarketDataSnapshot(Base):
    """Immutable candidate or approved provider import with full provenance."""

    __tablename__ = "market_data_snapshots"
    __table_args__ = {"schema": "diamond_market"}

    snapshot_id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=False, index=True,
    )
    snapshot_kind = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="candidate", server_default="candidate", index=True)
    currency_code = Column(String(3), nullable=False)
    unit = Column(String(32), nullable=False)
    source_url = Column(Text, nullable=False)
    methodology_url = Column(String(255), nullable=False)
    coverage_note = Column(Text, nullable=False)
    quote_count = Column(Integer, nullable=False)
    content_sha256 = Column(String(64), nullable=False)
    retrieved_at = Column(DateTime, nullable=False)
    created_by_id = Column(Integer, nullable=True)
    approved_by_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class MarketDataQuote(Base):
    """A normalized quote within exactly one immutable market snapshot."""

    __tablename__ = "market_data_quotes"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "shape_code", "carat_anchor", "color_code", "clarity_code",
            name="uix_market_snapshot_quote",
        ),
        {"schema": "diamond_market"},
    )

    quote_id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(
        Integer, ForeignKey("diamond_market.market_data_snapshots.snapshot_id"), nullable=False, index=True,
    )
    shape_code = Column(String(32), nullable=False)
    carat_anchor = Column(DECIMAL(8, 3), nullable=False)
    color_code = Column(String(16), nullable=False)
    clarity_code = Column(String(16), nullable=False)
    price_per_carat = Column(DECIMAL(14, 2), nullable=False)


class FxDataSnapshot(Base):
    """Immutable official FX response used when a valuation is attached."""

    __tablename__ = "fx_data_snapshots"
    __table_args__ = {"schema": "diamond_market"}

    fx_snapshot_id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=False, index=True,
    )
    base_currency_code = Column(String(3), nullable=False)
    quote_currency_code = Column(String(3), nullable=False)
    rate = Column(DECIMAL(18, 8), nullable=False)
    rate_date = Column(Date, nullable=False)
    source_url = Column(Text, nullable=False)
    retrieved_at = Column(DateTime, nullable=False)
    created_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class MarketProviderSchedule(Base):
    """Admin-owned execution and freshness policy for one provider."""

    __tablename__ = "market_provider_schedules"
    __table_args__ = {"schema": "diamond_market"}

    provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), primary_key=True,
    )
    enabled = Column(Boolean, nullable=False, default=True, server_default="1")
    timezone_name = Column(String(64), nullable=False, default="Europe/Kyiv", server_default="Europe/Kyiv")
    scheduled_hour = Column(Integer, nullable=False)
    scheduled_minute = Column(Integer, nullable=False)
    warn_after_hours = Column(Integer, nullable=False)
    block_after_hours = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class MarketProviderOperation(Base):
    """Immutable outcome of one manual or scheduled provider attempt."""

    __tablename__ = "market_provider_operations"
    __table_args__ = (
        Index("ix_market_operation_provider_started", "provider_code", "started_at"),
        {"schema": "diamond_market"},
    )

    operation_id = Column(Integer, primary_key=True)
    provider_code = Column(
        String(32), ForeignKey("diamond_market.market_data_providers.provider_code"), nullable=False,
    )
    trigger_type = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    market_snapshot_id = Column(Integer, nullable=True)
    fx_snapshot_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    initiated_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())



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
