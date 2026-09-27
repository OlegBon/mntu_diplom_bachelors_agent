"""Build or load the isolated deterministic synthetic demonstration dataset.

Without ``--apply`` this command is read-only and prints its manifest facts.
``--apply`` is deliberately explicit: it creates only ``DEMO-…`` rows and
never changes operational reports, external-provider snapshots, or accounts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from backend import models
from backend.calculator import DiamondCalculator
from backend.database import SessionLocal


DATASET_ID = "synthetic-demo-v2"
LEGACY_DATASET_ID = "synthetic-demo-v1"
GENERATOR_VERSION = "167-v2"
WORKFLOW_DATASET_ID = "synthetic-demo-v3"
WORKFLOW_LEGACY_DATASET_ID = DATASET_ID
WORKFLOW_GENERATOR_VERSION = "164-v3"
WORKFLOW_V4_DATASET_ID = "synthetic-demo-v4"
WORKFLOW_V4_LEGACY_DATASET_ID = WORKFLOW_DATASET_ID
WORKFLOW_V4_GENERATOR_VERSION = "164-v4"
DEFAULT_COUNT = 1_000
DEFAULT_SEED = 15_700
PROVENANCE = "synthetic-demo-v2; deterministic development-only records"
ELIGIBILITY = ["demo_operations", "synthetic_som", "demo_provider_analytics"]
RANGE_START = datetime(2023, 1, 3, 9, 0)
RANGE_END = datetime(2025, 12, 31, 9, 0)


@dataclass(frozen=True)
class DemoRecord:
    report_id: str
    report_date: str
    shape: str
    origin: str
    carat_weight: str
    color_grade: int
    clarity_grade: int
    table_percent: str
    depth_percent: str
    crown_angle: str
    pavilion_angle: str
    polish_grade: int
    symmetry_grade: int
    provider_a_usd: str
    provider_b_usd: str


@dataclass(frozen=True)
class SyntheticActorRecord:
    """A non-account identity used only by the v3 workflow demonstration."""

    actor_key: str
    display_name: str
    role: str
    sort_order: int


@dataclass(frozen=True)
class SyntheticActorProfile:
    """Declared synthetic workload profile; it never describes a real person."""

    actor: SyntheticActorRecord
    report_quota: int
    base_duration_seconds: int
    variation_seconds: int


@dataclass(frozen=True)
class SyntheticWorkflowRecord:
    """A reproducible workflow interval, not an operational user event."""

    report_id: str
    actor_key: str
    action: str
    occurred_at: str
    duration_seconds: int | None
    from_status: str | None = None
    to_status: str | None = None


@dataclass(frozen=True)
class ReplacementInventory:
    """Read-only ownership evidence required before replacing v1."""

    report_count: int
    stone_count: int
    event_count: int
    valuation_count: int
    media_count: int
    passport_count: int
    work_session_count: int
    work_session_event_count: int
    work_session_lease_count: int
    exact_expected_ids: bool

    @property
    def safe_to_replace(self) -> bool:
        return (
            self.report_count == DEFAULT_COUNT and self.stone_count == DEFAULT_COUNT
            and self.event_count == DEFAULT_COUNT * 2 and self.valuation_count == DEFAULT_COUNT * 2
            and self.media_count == self.passport_count == self.work_session_count == 0
            and self.work_session_event_count == self.work_session_lease_count == 0
            and self.exact_expected_ids
        )


@dataclass(frozen=True)
class WorkflowReplacementInventory:
    """Ownership evidence required before the v2 to v3 renewal."""

    report_count: int
    stone_count: int
    report_event_count: int
    valuation_count: int
    media_count: int
    passport_count: int
    work_session_count: int
    exact_expected_ids: bool

    @property
    def safe_to_replace(self) -> bool:
        return (
            self.report_count == DEFAULT_COUNT
            and self.stone_count == DEFAULT_COUNT
            and self.report_event_count == DEFAULT_COUNT * 2
            and self.valuation_count == DEFAULT_COUNT * 2
            and self.passport_count == self.work_session_count == 0
            and self.exact_expected_ids
        )


@dataclass(frozen=True)
class WorkflowV3ReplacementInventory:
    """Read-only evidence required before replacing the complete v3 graph."""

    report_count: int
    stone_count: int
    report_event_count: int
    valuation_count: int
    actor_count: int
    workflow_event_count: int
    media_count: int
    passport_count: int
    work_session_count: int
    exact_expected_ids: bool

    @property
    def safe_to_replace(self) -> bool:
        return (
            self.report_count == DEFAULT_COUNT
            and self.stone_count == DEFAULT_COUNT
            and self.report_event_count == DEFAULT_COUNT * 2
            and self.valuation_count == DEFAULT_COUNT * 2
            and self.actor_count == 6
            and self.workflow_event_count == DEFAULT_COUNT * 3
            and self.media_count == self.passport_count == self.work_session_count == 0
            and self.exact_expected_ids
        )


def build_records(*, count: int = DEFAULT_COUNT, seed: int = DEFAULT_SEED) -> list[DemoRecord]:
    """Return a reproducible, internally coherent population with no network I/O."""
    if count < 1 or count > 10_000:
        raise ValueError("count must be between 1 and 10000")
    rng = random.Random(seed)
    shapes = ("Round", "Oval", "Princess", "Emerald", "Cushion", "Pear")
    origins = ("natural", "natural", "natural", "lab_grown", "other")
    records: list[DemoRecord] = []
    interval_seconds = (RANGE_END - RANGE_START).total_seconds()
    for number in range(1, count + 1):
        carat = Decimal(str(round(rng.uniform(0.30, 3.20), 2)))
        table = Decimal(str(round(rng.uniform(54.0, 64.0), 2)))
        depth = Decimal(str(round(rng.uniform(59.0, 64.0), 2)))
        crown = Decimal(str(round(rng.uniform(32.5, 37.5), 2)))
        pavilion = Decimal(str(round(rng.uniform(40.1, 41.7), 2)))
        color = rng.randrange(0, 8)
        clarity = rng.randrange(0, 8)
        polish, symmetry = rng.choices(range(4), weights=(55, 30, 12, 3), k=2)
        base = Decimal("1800") * carat * Decimal(str(1 + (7 - color) * 0.12 + (7 - clarity) * 0.09))
        provider_a = base.quantize(Decimal("0.01"))
        provider_b = (base * Decimal(str(rng.uniform(0.90, 1.12)))).quantize(Decimal("0.01"))
        records.append(DemoRecord(
            report_id=f"DEMO-{number:05d}",
            report_date=(RANGE_START if count == 1 else RANGE_START + timedelta(seconds=interval_seconds * (number - 1) / (count - 1))).isoformat(),
            shape=rng.choice(shapes), origin=rng.choice(origins), carat_weight=str(carat),
            color_grade=color, clarity_grade=clarity, table_percent=str(table), depth_percent=str(depth),
            crown_angle=str(crown), pavilion_angle=str(pavilion), polish_grade=polish, symmetry_grade=symmetry,
            provider_a_usd=str(provider_a), provider_b_usd=str(provider_b),
        ))
    return records


def checksum(records: list[DemoRecord]) -> str:
    payload = json.dumps([asdict(record) for record in records], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_synthetic_actors() -> list[SyntheticActorRecord]:
    """Return stable fictional actors; these names never map to accounts."""
    return [
        SyntheticActorRecord("gemologist-01", "Synthetic Gemologist A", "gemologist", 1),
        SyntheticActorRecord("gemologist-02", "Synthetic Gemologist B", "gemologist", 2),
        SyntheticActorRecord("gemologist-03", "Synthetic Gemologist C", "gemologist", 3),
        SyntheticActorRecord("gemologist-04", "Synthetic Gemologist D", "gemologist", 4),
        SyntheticActorRecord("admin-01", "Synthetic Administrator A", "admin", 1),
        SyntheticActorRecord("admin-02", "Synthetic Administrator B", "admin", 2),
    ]


def build_synthetic_workflow(records: list[DemoRecord]) -> list[SyntheticWorkflowRecord]:
    """Assign deterministic synthetic intervals to every demo report."""
    events: list[SyntheticWorkflowRecord] = []
    for position, record in enumerate(records, start=1):
        created = datetime.fromisoformat(record.report_date)
        gemologist_key = f"gemologist-{((position - 1) % 4) + 1:02d}"
        admin_key = f"admin-{((position - 1) % 2) + 1:02d}"
        draft_seconds = 900 + (position * 37) % 2400
        review_seconds = 300 + (position * 19) % 1200
        events.extend((
            SyntheticWorkflowRecord(record.report_id, gemologist_key, "draft_completed", (created + timedelta(minutes=30)).isoformat(), draft_seconds),
            SyntheticWorkflowRecord(record.report_id, admin_key, "review_completed", (created + timedelta(minutes=90)).isoformat(), review_seconds),
            SyntheticWorkflowRecord(record.report_id, gemologist_key, "issued", (created + timedelta(hours=2)).isoformat(), None),
        ))
    return events


def build_synthetic_v4_profiles() -> tuple[list[SyntheticActorProfile], list[SyntheticActorProfile]]:
    """Return fixed unequal workload profiles for the v4 technical demonstration."""
    gemologists = [
        SyntheticActorProfile(SyntheticActorRecord("gemologist-01", "Synthetic Gemologist A", "gemologist", 1), 300, 1_320, 540),
        SyntheticActorProfile(SyntheticActorRecord("gemologist-02", "Synthetic Gemologist B", "gemologist", 2), 240, 1_620, 660),
        SyntheticActorProfile(SyntheticActorRecord("gemologist-03", "Synthetic Gemologist C", "gemologist", 3), 190, 2_040, 780),
        SyntheticActorProfile(SyntheticActorRecord("gemologist-04", "Synthetic Gemologist D", "gemologist", 4), 160, 2_520, 900),
        SyntheticActorProfile(SyntheticActorRecord("gemologist-05", "Synthetic Gemologist E", "gemologist", 5), 110, 3_060, 1_020),
    ]
    administrators = [
        SyntheticActorProfile(SyntheticActorRecord("admin-01", "Synthetic Administrator A", "admin", 1), 500, 720, 300),
        SyntheticActorProfile(SyntheticActorRecord("admin-02", "Synthetic Administrator B", "admin", 2), 320, 960, 420),
        SyntheticActorProfile(SyntheticActorRecord("admin-03", "Synthetic Administrator C", "admin", 3), 180, 1_320, 540),
    ]
    if sum(profile.report_quota for profile in gemologists) != DEFAULT_COUNT:
        raise RuntimeError("Synthetic gemologist quotas must cover every demo report")
    if sum(profile.report_quota for profile in administrators) != DEFAULT_COUNT:
        raise RuntimeError("Synthetic administrator quotas must cover every demo report")
    return gemologists, administrators


def _assign_profile_keys(records: list[DemoRecord], profiles: list[SyntheticActorProfile], *, seed: int) -> dict[str, SyntheticActorProfile]:
    """Assign exact profile quotas across the time range without round-robin bias."""
    shuffled_ids = [record.report_id for record in records]
    random.Random(seed).shuffle(shuffled_ids)
    assignments: dict[str, SyntheticActorProfile] = {}
    offset = 0
    for profile in profiles:
        for report_id in shuffled_ids[offset:offset + profile.report_quota]:
            assignments[report_id] = profile
        offset += profile.report_quota
    if len(assignments) != len(records):
        raise RuntimeError("Synthetic profile assignment did not cover every report")
    return assignments


def _synthetic_duration(profile: SyntheticActorProfile, record: DemoRecord, *, position: int, multiplier: int) -> int:
    """Produce a reproducible interval influenced by declared profile and stone complexity."""
    complexity = (
        int(Decimal(record.carat_weight) >= Decimal("2.00"))
        + int(record.shape != "Round")
        + int(record.clarity_grade >= 5)
        + int(record.color_grade >= 5)
    )
    span = profile.variation_seconds * 2 + 1
    jitter = ((position * multiplier) % span) - profile.variation_seconds
    return max(180, profile.base_duration_seconds + complexity * 150 + jitter)


def build_synthetic_v4_workflow(records: list[DemoRecord]) -> tuple[list[SyntheticActorRecord], list[SyntheticWorkflowRecord]]:
    """Build unequal deterministic actors, intervals and limited workflow outcomes for v4."""
    gemologist_profiles, administrator_profiles = build_synthetic_v4_profiles()
    gemologists = _assign_profile_keys(records, gemologist_profiles, seed=DEFAULT_SEED + 401)
    administrators = _assign_profile_keys(records, administrator_profiles, seed=DEFAULT_SEED + 809)
    events: list[SyntheticWorkflowRecord] = []
    for position, record in enumerate(records, start=1):
        created = datetime.fromisoformat(record.report_date)
        gemologist = gemologists[record.report_id]
        administrator = administrators[record.report_id]
        draft_seconds = _synthetic_duration(gemologist, record, position=position, multiplier=53)
        review_seconds = _synthetic_duration(administrator, record, position=position, multiplier=31)
        events.append(SyntheticWorkflowRecord(
            record.report_id, gemologist.actor.actor_key, "draft_completed",
            (created + timedelta(minutes=30)).isoformat(), draft_seconds,
        ))
        if position % 20 == 0:
            events.append(SyntheticWorkflowRecord(
                record.report_id, administrator.actor.actor_key, "review_voided",
                (created + timedelta(minutes=90)).isoformat(), review_seconds,
                "review", "void",
            ))
            continue
        if position % 7 == 0:
            events.extend((
                SyntheticWorkflowRecord(
                    record.report_id, administrator.actor.actor_key, "review_returned",
                    (created + timedelta(minutes=90)).isoformat(), review_seconds,
                    "review", "draft",
                ),
                SyntheticWorkflowRecord(
                    record.report_id, gemologist.actor.actor_key, "draft_reworked",
                    (created + timedelta(minutes=150)).isoformat(), max(180, draft_seconds // 2),
                ),
                SyntheticWorkflowRecord(
                    record.report_id, administrator.actor.actor_key, "review_completed",
                    (created + timedelta(minutes=210)).isoformat(), max(180, review_seconds // 2),
                    "review", "issued",
                ),
            ))
        else:
            events.append(SyntheticWorkflowRecord(
                record.report_id, administrator.actor.actor_key, "review_completed",
                (created + timedelta(minutes=90)).isoformat(), review_seconds,
                "review", "issued",
            ))
        events.append(SyntheticWorkflowRecord(
            record.report_id, gemologist.actor.actor_key, "issued",
            (created + timedelta(hours=2)).isoformat(), None, "review", "issued",
        ))
    actors = [profile.actor for profile in gemologist_profiles + administrator_profiles]
    return actors, events


def workflow_checksum(
    records: list[DemoRecord], actors: list[SyntheticActorRecord], workflow: list[SyntheticWorkflowRecord],
) -> str:
    payload = json.dumps(
        {"reports": [asdict(record) for record in records], "actors": [asdict(actor) for actor in actors], "workflow": [asdict(event) for event in workflow]},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def workflow_final_statuses(workflow: list[SyntheticWorkflowRecord]) -> dict[str, str]:
    """Derive one final synthetic lifecycle state per report from ordered workflow records."""
    statuses: dict[str, str] = {}
    for event in workflow:
        if event.to_status in {"issued", "void"}:
            statuses[event.report_id] = event.to_status
    return statuses


def apply_dataset(
    db: Session,
    records: list[DemoRecord],
    *,
    commit: bool = True,
    dataset_id: str = DATASET_ID,
    version: str = "v2",
    generator_version: str = GENERATOR_VERSION,
    provenance: str = PROVENANCE,
    content_sha256: str | None = None,
    final_statuses: dict[str, str] | None = None,
) -> bool:
    """Insert one whole dataset once; refuse partial or incompatible reruns."""
    digest = content_sha256 or checksum(records)
    existing = db.get(models.DemoDataset, dataset_id)
    existing_count = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo", models.DiamondReport.demo_dataset_id == dataset_id,
    ).count()
    if existing is not None:
        if existing.content_sha256 != digest or existing.record_count != len(records) or existing_count != len(records):
            raise RuntimeError("Existing demo dataset does not match this generator; no changes were made")
        return False
    if existing_count:
        raise RuntimeError("Demo rows exist without a manifest; no changes were made")
    manifest = models.DemoDataset(
        dataset_id=dataset_id, label="Synthetic demonstration dataset", version=version,
        generator_version=generator_version, content_sha256=digest, provenance=provenance,
        scope_note="Internal synthetic development demo; not market, training, sale, or investment data.",
        analysis_eligibility=json.dumps(ELIGIBILITY), record_count=len(records),
    )
    db.add(manifest)
    for record in records:
        report_date = datetime.fromisoformat(record.report_date)
        final_status = (final_statuses or {}).get(record.report_id, "issued")
        if final_status not in {"issued", "void"}:
            raise RuntimeError("Synthetic final report status must be issued or void")
        proportions = DiamondCalculator.evaluate_proportions(float(record.table_percent), float(record.depth_percent), float(record.crown_angle), float(record.pavilion_angle))
        cut = DiamondCalculator.calculate_final_cut(proportions, record.polish_grade, record.symmetry_grade)
        diameter = (Decimal(record.carat_weight) ** Decimal("0.333333")).quantize(Decimal("0.01")) * Decimal("6.40")
        stone = models.Stone(
            shape=record.shape, carat_weight=Decimal(record.carat_weight),
            color_grade=record.color_grade, clarity_grade=record.clarity_grade,
            measurements_length=diameter, measurements_width=diameter, measurements_depth=(diameter * Decimal(record.depth_percent) / 100).quantize(Decimal("0.01")),
            table_percent=Decimal(record.table_percent), depth_percent=Decimal(record.depth_percent), crown_angle=Decimal(record.crown_angle), pavilion_angle=Decimal(record.pavilion_angle),
            girdle_thickness="medium", culet_size="none", polish_grade=record.polish_grade,
            symmetry_grade=record.symmetry_grade, fluorescence_grade=0, origin=record.origin,
            treatment_status="not_assessed", identification_status="preliminary", market_status="not_for_sale",
            identification_method="Synthetic development sample", identification_conclusion="Synthetic record; not an expert conclusion.",
            created_at=report_date, updated_at=report_date,
        )
        db.add(stone); db.flush()
        report = models.DiamondReport(
            report_id=record.report_id, record_scope="demo", demo_dataset_id=dataset_id,
            report_date=report_date, examination_date=report_date.date(), stone_id=stone.stone_id,
            status=final_status, created_at=report_date, updated_at=report_date,
            issued_at=report_date + timedelta(hours=2) if final_status == "issued" else None,
            system_proportions_grade=proportions, system_cut_grade=cut, calculation_rule_version="idc-demo-v1",
            expert_proportions_grade=proportions, expert_cut_grade=cut, expert_confirmed_at=report_date + timedelta(hours=1),
            shape=record.shape, carat_weight=Decimal(record.carat_weight), color_grade=record.color_grade,
            clarity_grade=record.clarity_grade, cut_grade=cut, polish_grade=record.polish_grade,
            symmetry_grade=record.symmetry_grade, proportions_grade=proportions, fluorescence_grade=0,
            expert_comment="Synthetic demonstration record. No real expert, customer, or transaction data.",
            report_notes_length=10,
            report_sentiment=0,
        )
        db.add(report)
        # MariaDB enforces the ReportEvent foreign key immediately. Flush the
        # parent before adding its append-only child events (SQLite tests do
        # not expose this ordering difference by default).
        db.flush()
        db.add(models.ReportEvent(report_id=record.report_id, action="created", to_status="draft", reason="Synthetic demonstration dataset", created_at=report_date))
        db.add(models.ReportEvent(
            report_id=record.report_id,
            action="status_changed",
            from_status="draft",
            to_status=final_status,
            reason="Synthetic internal demonstration state",
            created_at=report_date + timedelta(hours=2),
        ))
        for source_name, amount in (("Demo Market A", record.provider_a_usd), ("Demo Market B", record.provider_b_usd)):
            db.add(models.StoneValuation(stone_id=stone.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal(amount), currency_code="USD", unit="TOTAL_STONE", source_name=source_name, source_reference=f"{dataset_id}/{source_name.replace(' ', '-').lower()}/{version}", applicability_note="Synthetic demonstration reference only.", observed_at=report_date))
    if commit:
        db.commit()
    return True


def apply_workflow_dataset(
    db: Session,
    records: list[DemoRecord],
    actors: list[SyntheticActorRecord],
    workflow: list[SyntheticWorkflowRecord],
    *,
    commit: bool = True,
    dataset_id: str = WORKFLOW_DATASET_ID,
    version: str = "v3",
    generator_version: str = WORKFLOW_GENERATOR_VERSION,
    provenance: str = "synthetic-demo-v3; deterministic development-only workflow records",
) -> bool:
    """Create one manifest-authorized, deterministic synthetic workflow dataset."""
    digest = workflow_checksum(records, actors, workflow)
    existing = db.get(models.DemoDataset, dataset_id)
    if existing is not None:
        actual = {
            "reports": db.query(models.DiamondReport).filter(models.DiamondReport.demo_dataset_id == dataset_id).count(),
            "actors": db.query(models.DemoSyntheticActor).filter(models.DemoSyntheticActor.dataset_id == dataset_id).count(),
            "workflow": db.query(models.DemoWorkflowEvent).filter(models.DemoWorkflowEvent.dataset_id == dataset_id).count(),
        }
        expected = {"reports": len(records), "actors": len(actors), "workflow": len(workflow)}
        if existing.content_sha256 != digest or actual != expected:
            raise RuntimeError("Existing demo workflow dataset does not match this generator; no changes were made")
        return False

    final_statuses = workflow_final_statuses(workflow)
    created = apply_dataset(
        db, records, commit=False, dataset_id=dataset_id, version=version,
        generator_version=generator_version, provenance=provenance, content_sha256=digest,
        final_statuses=final_statuses,
    )
    if not created:
        return False
    for actor in actors:
        db.add(models.DemoSyntheticActor(
            dataset_id=dataset_id, actor_key=actor.actor_key,
            display_name=actor.display_name, role=actor.role, sort_order=actor.sort_order,
        ))
    db.flush()
    actor_ids = {
        actor.actor_key: actor.actor_id
        for actor in db.query(models.DemoSyntheticActor).filter(
            models.DemoSyntheticActor.dataset_id == dataset_id,
        )
    }
    for event in workflow:
        db.add(models.DemoWorkflowEvent(
            dataset_id=dataset_id, report_id=event.report_id,
            actor_id=actor_ids[event.actor_key], action=event.action,
            occurred_at=datetime.fromisoformat(event.occurred_at), duration_seconds=event.duration_seconds,
            from_status=event.from_status, to_status=event.to_status,
        ))
    if commit:
        db.commit()
    return True


def _expected_report_ids() -> set[str]:
    return {f"DEMO-{number:05d}" for number in range(1, DEFAULT_COUNT + 1)}


def inventory_legacy_v1(db: Session) -> ReplacementInventory:
    """Read exactly the v1-owned dependency graph; this function never writes."""
    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    work_sessions = db.query(models.ReportWorkSession).filter(
        models.ReportWorkSession.report_id.in_(report_ids) if report_ids else False,
    ).all()
    work_session_ids = [session.work_session_id for session in work_sessions]
    return ReplacementInventory(
        report_count=len(reports),
        stone_count=len(stone_ids),
        event_count=db.query(models.ReportEvent).filter(models.ReportEvent.report_id.in_(report_ids) if report_ids else False).count(),
        valuation_count=db.query(models.StoneValuation).filter(models.StoneValuation.stone_id.in_(stone_ids) if stone_ids else False).count(),
        media_count=db.query(models.MediaAsset).filter(models.MediaAsset.report_id.in_(report_ids) if report_ids else False).count(),
        passport_count=db.query(models.PublicPassport).filter(models.PublicPassport.report_id.in_(report_ids) if report_ids else False).count(),
        work_session_count=len(work_sessions),
        work_session_event_count=db.query(models.ReportWorkSessionEvent).filter(models.ReportWorkSessionEvent.work_session_id.in_(work_session_ids) if work_session_ids else False).count(),
        work_session_lease_count=db.query(models.ReportWorkSessionLease).filter(models.ReportWorkSessionLease.report_id.in_(report_ids) if report_ids else False).count(),
        exact_expected_ids=set(report_ids) == _expected_report_ids(),
    )


def inventory_workflow_legacy_v2(db: Session) -> WorkflowReplacementInventory:
    """Read only the v2-owned graph; do not infer ownership from ID prefixes."""
    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == WORKFLOW_LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    return WorkflowReplacementInventory(
        report_count=len(reports),
        stone_count=len(stone_ids),
        report_event_count=db.query(models.ReportEvent).filter(
            models.ReportEvent.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        valuation_count=db.query(models.StoneValuation).filter(
            models.StoneValuation.stone_id.in_(stone_ids) if stone_ids else False,
        ).count(),
        media_count=db.query(models.MediaAsset).filter(
            models.MediaAsset.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        passport_count=db.query(models.PublicPassport).filter(
            models.PublicPassport.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        work_session_count=db.query(models.ReportWorkSession).filter(
            models.ReportWorkSession.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        exact_expected_ids=set(report_ids) == _expected_report_ids(),
    )


def inventory_workflow_legacy_v3(db: Session) -> WorkflowV3ReplacementInventory:
    """Read exactly the v3-owned graph before any v4 replacement."""
    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    return WorkflowV3ReplacementInventory(
        report_count=len(reports),
        stone_count=len(stone_ids),
        report_event_count=db.query(models.ReportEvent).filter(
            models.ReportEvent.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        valuation_count=db.query(models.StoneValuation).filter(
            models.StoneValuation.stone_id.in_(stone_ids) if stone_ids else False,
        ).count(),
        actor_count=db.query(models.DemoSyntheticActor).filter(
            models.DemoSyntheticActor.dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
        ).count(),
        workflow_event_count=db.query(models.DemoWorkflowEvent).filter(
            models.DemoWorkflowEvent.dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
        ).count(),
        media_count=db.query(models.MediaAsset).filter(
            models.MediaAsset.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        passport_count=db.query(models.PublicPassport).filter(
            models.PublicPassport.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        work_session_count=db.query(models.ReportWorkSession).filter(
            models.ReportWorkSession.report_id.in_(report_ids) if report_ids else False,
        ).count(),
        exact_expected_ids=set(report_ids) == _expected_report_ids(),
    )


def replacement_preview(records: list[DemoRecord], inventory: ReplacementInventory | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "dataset_id": DATASET_ID,
        "replaces_dataset_id": LEGACY_DATASET_ID,
        "record_count": len(records),
        "content_sha256": checksum(records),
        "first_report": {"report_id": records[0].report_id, "report_date": records[0].report_date},
        "last_report": {"report_id": records[-1].report_id, "report_date": records[-1].report_date},
        "showcase_report_id": "DEMO-00999",
        "read_only": True,
    }
    if inventory is not None:
        result["v1_inventory"] = asdict(inventory)
        result["ready_for_replace"] = inventory.safe_to_replace
    return result


def workflow_replacement_preview(
    records: list[DemoRecord], actors: list[SyntheticActorRecord], workflow: list[SyntheticWorkflowRecord],
    inventory: WorkflowReplacementInventory | None = None,
) -> dict[str, object]:
    """Describe v3 creation without reading or changing the database."""
    preview: dict[str, object] = {
        "dataset_id": WORKFLOW_DATASET_ID,
        "replaces_dataset_id": WORKFLOW_LEGACY_DATASET_ID,
        "record_count": len(records),
        "actor_count": len(actors),
        "workflow_event_count": len(workflow),
        "content_sha256": workflow_checksum(records, actors, workflow),
        "read_only": True,
        "requires_backup_and_explicit_replace_confirmation": True,
    }
    if inventory is not None:
        preview["v2_inventory"] = asdict(inventory)
        preview["ready_for_replace"] = inventory.safe_to_replace
    return preview


def workflow_v4_replacement_preview(
    records: list[DemoRecord], actors: list[SyntheticActorRecord], workflow: list[SyntheticWorkflowRecord],
    inventory: WorkflowV3ReplacementInventory | None = None,
) -> dict[str, object]:
    """Describe the proposed unequal v4 demo graph without writing any rows."""
    actor_reports: dict[str, set[str]] = {actor.actor_key: set() for actor in actors}
    for event in workflow:
        actor_reports[event.actor_key].add(event.report_id)
    final_statuses = workflow_final_statuses(workflow)
    preview: dict[str, object] = {
        "dataset_id": WORKFLOW_V4_DATASET_ID,
        "replaces_dataset_id": WORKFLOW_V4_LEGACY_DATASET_ID,
        "record_count": len(records),
        "actor_count": len(actors),
        "workflow_event_count": len(workflow),
        "actor_report_assignments": {actor.actor_key: len(actor_reports[actor.actor_key]) for actor in actors},
        "final_status_counts": {status: list(final_statuses.values()).count(status) for status in ("issued", "void")},
        "content_sha256": workflow_checksum(records, actors, workflow),
        "read_only": True,
        "requires_backup_and_explicit_replace_confirmation": True,
    }
    if inventory is not None:
        preview["v3_inventory"] = asdict(inventory)
        preview["ready_for_replace"] = inventory.safe_to_replace
    return preview


def replace_legacy_v1(db: Session, records: list[DemoRecord]) -> None:
    """Atomically replace only a fully verified v1 dataset with v2."""
    inventory = inventory_legacy_v1(db)
    if not inventory.safe_to_replace:
        raise RuntimeError("Legacy v1 inventory is not safe to replace; no changes were made")
    if db.get(models.DemoDataset, DATASET_ID) is not None:
        raise RuntimeError("Synthetic demo v2 manifest already exists; no changes were made")

    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    try:
        db.query(models.ReportEvent).filter(models.ReportEvent.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.StoneValuation).filter(models.StoneValuation.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DiamondReport).filter(models.DiamondReport.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.Stone).filter(models.Stone.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DemoDataset).filter(models.DemoDataset.dataset_id == LEGACY_DATASET_ID).delete(synchronize_session=False)
        db.flush()
        # The replacement intentionally reuses global DEMO IDs.  Remove stale
        # deleted ORM identities before inserting their v2 counterparts.
        db.expunge_all()
        apply_dataset(db, records, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise


def replace_workflow_legacy_v2(
    db: Session, records: list[DemoRecord], actors: list[SyntheticActorRecord], workflow: list[SyntheticWorkflowRecord],
) -> None:
    """Atomically renew the verified v2 graph into immutable v3 workflow data."""
    inventory = inventory_workflow_legacy_v2(db)
    if not inventory.safe_to_replace:
        raise RuntimeError("Legacy v2 inventory is not safe to replace; no changes were made")
    if db.get(models.DemoDataset, WORKFLOW_DATASET_ID) is not None:
        raise RuntimeError("Synthetic demo v3 manifest already exists; no changes were made")
    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == WORKFLOW_LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    try:
        db.query(models.DemoWorkflowEvent).filter(
            models.DemoWorkflowEvent.dataset_id == WORKFLOW_LEGACY_DATASET_ID,
        ).delete(synchronize_session=False)
        db.query(models.DemoSyntheticActor).filter(
            models.DemoSyntheticActor.dataset_id == WORKFLOW_LEGACY_DATASET_ID,
        ).delete(synchronize_session=False)
        db.query(models.ReportEvent).filter(models.ReportEvent.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.MediaAsset).filter(models.MediaAsset.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.StoneValuation).filter(models.StoneValuation.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DiamondReport).filter(models.DiamondReport.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.Stone).filter(models.Stone.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DemoDataset).filter(
            models.DemoDataset.dataset_id == WORKFLOW_LEGACY_DATASET_ID,
        ).delete(synchronize_session=False)
        db.flush()
        db.expunge_all()
        apply_workflow_dataset(db, records, actors, workflow, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise


def replace_workflow_legacy_v3(
    db: Session, records: list[DemoRecord], actors: list[SyntheticActorRecord], workflow: list[SyntheticWorkflowRecord],
) -> None:
    """Atomically replace only the verified v3 synthetic graph with v4."""
    inventory = inventory_workflow_legacy_v3(db)
    if not inventory.safe_to_replace:
        raise RuntimeError("Legacy v3 inventory is not safe to replace; no changes were made")
    if db.get(models.DemoDataset, WORKFLOW_V4_DATASET_ID) is not None:
        raise RuntimeError("Synthetic demo v4 manifest already exists; no changes were made")
    reports = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo",
        models.DiamondReport.demo_dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
    ).all()
    report_ids = [report.report_id for report in reports]
    stone_ids = [report.stone_id for report in reports if report.stone_id is not None]
    try:
        db.query(models.DemoWorkflowEvent).filter(
            models.DemoWorkflowEvent.dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
        ).delete(synchronize_session=False)
        db.query(models.DemoSyntheticActor).filter(
            models.DemoSyntheticActor.dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID,
        ).delete(synchronize_session=False)
        db.query(models.ReportEvent).filter(models.ReportEvent.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.MediaAsset).filter(models.MediaAsset.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.StoneValuation).filter(models.StoneValuation.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DiamondReport).filter(models.DiamondReport.report_id.in_(report_ids)).delete(synchronize_session=False)
        db.query(models.Stone).filter(models.Stone.stone_id.in_(stone_ids)).delete(synchronize_session=False)
        db.query(models.DemoDataset).filter(models.DemoDataset.dataset_id == WORKFLOW_V4_LEGACY_DATASET_ID).delete(synchronize_session=False)
        db.flush()
        db.expunge_all()
        apply_workflow_dataset(
            db, records, actors, workflow, commit=False,
            dataset_id=WORKFLOW_V4_DATASET_ID, version="v4",
            generator_version=WORKFLOW_V4_GENERATOR_VERSION,
            provenance="synthetic-demo-v4; deterministic unequal workload demonstration records",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create v2 only when no demo manifest exists")
    parser.add_argument("--dry-run-replace-v1", action="store_true", help="Read v1 ownership inventory; never writes")
    parser.add_argument("--replace-v1", action="store_true", help="Replace verified v1 rows with v2")
    parser.add_argument("--confirm-replace-v1", action="store_true", help="Required together with --replace-v1")
    parser.add_argument("--dry-run-replace-v2", action="store_true", help="Read v2 ownership inventory; never writes")
    parser.add_argument("--replace-v2", action="store_true", help="Replace verified v2 rows with v3 workflow data")
    parser.add_argument("--confirm-replace-v2", action="store_true", help="Required together with --replace-v2")
    parser.add_argument("--dry-run-replace-v3", action="store_true", help="Read v3 ownership inventory; never writes")
    parser.add_argument("--replace-v3", action="store_true", help="Replace verified v3 rows with v4 unequal workflow data")
    parser.add_argument("--confirm-replace-v3", action="store_true", help="Required together with --replace-v3")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    records = build_records(count=args.count, seed=args.seed)
    actors = build_synthetic_actors()
    workflow = build_synthetic_workflow(records)
    v4_actors, v4_workflow = build_synthetic_v4_workflow(records)
    if args.replace_v1 and not args.confirm_replace_v1:
        parser.error("--replace-v1 requires --confirm-replace-v1")
    if args.replace_v2 and not args.confirm_replace_v2:
        parser.error("--replace-v2 requires --confirm-replace-v2")
    if args.replace_v3 and not args.confirm_replace_v3:
        parser.error("--replace-v3 requires --confirm-replace-v3")
    if args.apply and any((
        args.replace_v1, args.dry_run_replace_v1, args.replace_v2, args.dry_run_replace_v2,
        args.replace_v3, args.dry_run_replace_v3,
    )):
        parser.error("--apply cannot be combined with replacement options")
    if args.dry_run_replace_v1:
        with SessionLocal() as db:
            print(json.dumps(replacement_preview(records, inventory_legacy_v1(db)), ensure_ascii=False, indent=2))
        return
    if args.dry_run_replace_v2:
        with SessionLocal() as db:
            print(json.dumps(workflow_replacement_preview(records, actors, workflow, inventory_workflow_legacy_v2(db)), ensure_ascii=False, indent=2))
        return
    if args.dry_run_replace_v3:
        with SessionLocal() as db:
            print(json.dumps(
                workflow_v4_replacement_preview(records, v4_actors, v4_workflow, inventory_workflow_legacy_v3(db)),
                ensure_ascii=False,
                indent=2,
            ))
        return
    if args.replace_v1:
        with SessionLocal() as db:
            replace_legacy_v1(db, records)
        result = replacement_preview(records)
        result["read_only"] = False
        result["replaced"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.replace_v2:
        with SessionLocal() as db:
            replace_workflow_legacy_v2(db, records, actors, workflow)
        result = workflow_replacement_preview(records, actors, workflow)
        result["read_only"] = False
        result["replaced"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.replace_v3:
        with SessionLocal() as db:
            replace_workflow_legacy_v3(db, records, v4_actors, v4_workflow)
        result = workflow_v4_replacement_preview(records, v4_actors, v4_workflow)
        result["read_only"] = False
        result["replaced"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    result = replacement_preview(records)
    if args.apply:
        with SessionLocal() as db:
            try:
                result["created"] = apply_dataset(db, records)
                result["read_only"] = False
            except Exception:
                db.rollback()
                raise
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
