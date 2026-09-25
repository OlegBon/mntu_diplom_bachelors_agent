from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest

from backend import models


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_generator_module():
    module_path = PROJECT_ROOT / "scripts" / "generate_synthetic_demo_dataset.py"
    spec = spec_from_file_location("generate_synthetic_demo_dataset", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_records_are_deterministic_and_use_only_demo_identifiers():
    module = load_generator_module()

    first = module.build_records(count=5, seed=15700)
    second = module.build_records(count=5, seed=15700)

    assert first == second
    assert module.checksum(first) == module.checksum(second)
    assert [record.report_id for record in first] == [
        "DEMO-00001", "DEMO-00002", "DEMO-00003", "DEMO-00004", "DEMO-00005",
    ]
    assert {record.origin for record in first} <= {"natural", "lab_grown", "other"}
    assert all(record.provider_a_usd != record.provider_b_usd for record in first)


def test_apply_creates_an_isolated_dataset_once_without_accounts_or_passports(db_session):
    module = load_generator_module()
    records = module.build_records(count=3, seed=15700)

    assert module.apply_dataset(db_session, records) is True
    assert module.apply_dataset(db_session, records) is False

    manifest = db_session.get(models.DemoDataset, module.DATASET_ID)
    reports = db_session.query(models.DiamondReport).order_by(models.DiamondReport.report_id).all()
    events = db_session.query(models.ReportEvent).all()
    valuations = db_session.query(models.StoneValuation).all()

    assert manifest is not None
    assert manifest.record_count == 3
    assert manifest.content_sha256 == module.checksum(records)
    assert [report.report_id for report in reports] == ["DEMO-00001", "DEMO-00002", "DEMO-00003"]
    assert all(report.record_scope == "demo" and report.demo_dataset_id == module.DATASET_ID for report in reports)
    assert all(report.expert_id is None and report.issued_by_id is None and report.price is None for report in reports)
    assert len(events) == 6 and all(event.actor_id is None for event in events)
    assert len(valuations) == 6
    assert {value.source_name for value in valuations} == {"Demo Market A", "Demo Market B"}
    assert {value.valuation_kind for value in valuations} == {"synthetic_demo_reference"}
    assert db_session.query(models.Expert).count() == 0
    assert db_session.query(models.PublicPassport).count() == 0


def test_incompatible_rerun_is_rejected_without_altering_dataset(db_session):
    module = load_generator_module()
    module.apply_dataset(db_session, module.build_records(count=3, seed=15700))

    with pytest.raises(RuntimeError, match="does not match"):
        module.apply_dataset(db_session, module.build_records(count=4, seed=15700))

    assert db_session.query(models.DiamondReport).count() == 3
    assert db_session.get(models.DemoDataset, module.DATASET_ID).record_count == 3
