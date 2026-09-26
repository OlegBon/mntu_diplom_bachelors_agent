from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_generator_module():
    module_path = PROJECT_ROOT / "scripts" / "generate_synthetic_demo_dataset.py"
    spec = spec_from_file_location("generate_synthetic_demo_dataset_v4", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v4_workflow_has_deterministic_unequal_actor_profiles_and_outcomes():
    module = load_generator_module()
    records = module.build_records()
    actors, workflow = module.build_synthetic_v4_workflow(records)
    duplicate_actors, duplicate_workflow = module.build_synthetic_v4_workflow(records)

    assignments = Counter(event.actor_key for event in workflow if event.action == "draft_completed")
    review_assignments = {
        actor_key: len({event.report_id for event in workflow if event.actor_key == actor_key and event.action in {"review_completed", "review_returned", "review_voided"}})
        for actor_key in ("admin-01", "admin-02", "admin-03")
    }
    preview = module.workflow_v4_replacement_preview(records, actors, workflow)

    assert [actor.role for actor in actors] == ["gemologist"] * 5 + ["admin"] * 3
    assert assignments == {
        "gemologist-01": 300,
        "gemologist-02": 240,
        "gemologist-03": 190,
        "gemologist-04": 160,
        "gemologist-05": 110,
    }
    assert review_assignments == {
        "admin-01": 500,
        "admin-02": 320,
        "admin-03": 180,
    }
    assert any(event.action == "review_returned" for event in workflow)
    assert any(event.action == "review_voided" for event in workflow)
    assert module.workflow_checksum(records, actors, workflow) == module.workflow_checksum(records, duplicate_actors, duplicate_workflow)
    assert preview["dataset_id"] == "synthetic-demo-v4"
    assert preview["final_status_counts"]["void"] == 50
