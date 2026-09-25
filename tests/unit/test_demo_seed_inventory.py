from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_inventory_module():
    module_path = PROJECT_ROOT / "scripts" / "inventory_demo_seed.py"
    spec = spec_from_file_location("inventory_demo_seed", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_seed_inventory_uses_exact_historical_range():
    module = load_inventory_module()

    expected = module.expected_report_ids()

    assert len(expected) == 1_000
    assert "DR-00001" in expected
    assert "DR-01000" in expected
    assert "DR-01001" not in expected
