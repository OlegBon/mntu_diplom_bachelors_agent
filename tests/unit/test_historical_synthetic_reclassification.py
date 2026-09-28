from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_module():
    spec = spec_from_file_location("historical_reclassification", PROJECT_ROOT / "scripts" / "historical_synthetic_reclassification.py")
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_allow_list_requires_unique_explicit_dr_ids(tmp_path):
    module = load_module()
    allow_list = tmp_path / "allow-list.json"
    allow_list.write_text(
        '{"reviewed_candidate_ids": ["DR-00002", "DR-00001"], '
        '"approved_report_ids": ["DR-00002", "DR-00001"]}',
        encoding="utf-8",
    )
    assert module.load_allow_list(allow_list) == ["DR-00001", "DR-00002"]
    assert len(module.allow_list_sha256(["DR-00001", "DR-00002"])) == 64

    allow_list.write_text(
        '{"reviewed_candidate_ids": ["DR-00001", "DR-00001"], '
        '"approved_report_ids": ["DR-00001", "DR-00001"]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        module.load_allow_list(allow_list)


def test_allow_list_rejects_candidate_inventory_mismatch(tmp_path):
    module = load_module()
    allow_list = tmp_path / "allow-list.json"
    allow_list.write_text(
        '{"reviewed_candidate_ids": ["DR-00001", "DR-00002"], '
        '"approved_report_ids": ["DR-00001"]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="differs"):
        module.load_allow_list(allow_list)
