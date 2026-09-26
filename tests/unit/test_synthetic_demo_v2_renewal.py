from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_generator_module():
    module_path = PROJECT_ROOT / "scripts" / "generate_synthetic_demo_dataset.py"
    spec = spec_from_file_location("generate_synthetic_demo_dataset_v2", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v2_uses_the_declared_inclusive_three_year_date_range():
    module = load_generator_module()

    records = module.build_records()

    assert records[0].report_id == "DEMO-00001"
    assert records[0].report_date == "2023-01-03T09:00:00"
    assert records[-1].report_id == "DEMO-01000"
    assert records[-1].report_date == "2025-12-31T09:00:00"
    assert [record.report_date for record in records] == sorted(record.report_date for record in records)
    assert module.build_records(count=1)[0].report_date == "2023-01-03T09:00:00"


def test_replacement_preview_is_pure_and_marks_an_empty_database_unsafe(db_session):
    module = load_generator_module()
    records = module.build_records(count=3)

    inventory = module.inventory_legacy_v1(db_session)
    preview = module.replacement_preview(records, inventory)

    assert inventory.safe_to_replace is False
    assert preview["read_only"] is True
    assert preview["dataset_id"] == "synthetic-demo-v2"
    assert preview["replaces_dataset_id"] == "synthetic-demo-v1"
    assert preview["last_report"]["report_id"] == "DEMO-00003"
    assert preview["ready_for_replace"] is False
