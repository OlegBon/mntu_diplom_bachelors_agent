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


DATASET_ID = "synthetic-demo-v1"
GENERATOR_VERSION = "157-v1"
DEFAULT_COUNT = 1_000
DEFAULT_SEED = 15_700
PROVENANCE = "synthetic-demo-v1; deterministic development-only records"
ELIGIBILITY = ["demo_operations", "synthetic_som"]


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


def build_records(*, count: int = DEFAULT_COUNT, seed: int = DEFAULT_SEED) -> list[DemoRecord]:
    """Return a reproducible, internally coherent population with no network I/O."""
    if count < 1 or count > 10_000:
        raise ValueError("count must be between 1 and 10000")
    rng = random.Random(seed)
    shapes = ("Round", "Oval", "Princess", "Emerald", "Cushion", "Pear")
    origins = ("natural", "natural", "natural", "lab_grown", "other")
    records: list[DemoRecord] = []
    start = datetime(2023, 1, 3, 9, 0)
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
            report_date=(start + timedelta(days=(number - 1) * 1095 / count)).isoformat(),
            shape=rng.choice(shapes), origin=rng.choice(origins), carat_weight=str(carat),
            color_grade=color, clarity_grade=clarity, table_percent=str(table), depth_percent=str(depth),
            crown_angle=str(crown), pavilion_angle=str(pavilion), polish_grade=polish, symmetry_grade=symmetry,
            provider_a_usd=str(provider_a), provider_b_usd=str(provider_b),
        ))
    return records


def checksum(records: list[DemoRecord]) -> str:
    payload = json.dumps([asdict(record) for record in records], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def apply_dataset(db: Session, records: list[DemoRecord]) -> bool:
    """Insert one whole dataset once; refuse partial or incompatible reruns."""
    digest = checksum(records)
    existing = db.get(models.DemoDataset, DATASET_ID)
    existing_count = db.query(models.DiamondReport).filter(
        models.DiamondReport.record_scope == "demo", models.DiamondReport.demo_dataset_id == DATASET_ID,
    ).count()
    if existing is not None:
        if existing.content_sha256 != digest or existing.record_count != len(records) or existing_count != len(records):
            raise RuntimeError("Existing demo dataset does not match this generator; no changes were made")
        return False
    if existing_count:
        raise RuntimeError("Demo rows exist without a manifest; no changes were made")
    manifest = models.DemoDataset(
        dataset_id=DATASET_ID, label="Synthetic demonstration dataset", version="v1",
        generator_version=GENERATOR_VERSION, content_sha256=digest, provenance=PROVENANCE,
        scope_note="Internal synthetic development demo; not market, training, sale, or investment data.",
        analysis_eligibility=json.dumps(ELIGIBILITY), record_count=len(records),
    )
    db.add(manifest)
    for record in records:
        report_date = datetime.fromisoformat(record.report_date)
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
            report_id=record.report_id, record_scope="demo", demo_dataset_id=DATASET_ID,
            report_date=report_date, examination_date=report_date.date(), stone_id=stone.stone_id,
            status="issued", created_at=report_date, updated_at=report_date, issued_at=report_date + timedelta(hours=2),
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
        db.add(models.ReportEvent(report_id=record.report_id, action="status_changed", from_status="draft", to_status="issued", reason="Synthetic internal demonstration state", created_at=report_date + timedelta(hours=2)))
        for source_name, amount in (("Demo Market A", record.provider_a_usd), ("Demo Market B", record.provider_b_usd)):
            db.add(models.StoneValuation(stone_id=stone.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal(amount), currency_code="USD", unit="TOTAL_STONE", source_name=source_name, source_reference=f"{DATASET_ID}/{source_name.replace(' ', '-').lower()}/v1", applicability_note="Synthetic demonstration reference only.", observed_at=report_date))
    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    records = build_records(count=args.count, seed=args.seed)
    result = {"dataset_id": DATASET_ID, "record_count": len(records), "content_sha256": checksum(records), "read_only": not args.apply}
    if args.apply:
        with SessionLocal() as db:
            try:
                result["created"] = apply_dataset(db, records)
            except Exception:
                db.rollback()
                raise
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
