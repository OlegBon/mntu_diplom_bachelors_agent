from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_generator_module():
    module_path = PROJECT_ROOT / "scripts" / "generate_synthetic_demo_dataset.py"
    spec = spec_from_file_location("generate_synthetic_demo_dataset_v3", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v3_workflow_is_deterministic_and_uses_only_synthetic_actors():
    module = load_generator_module()

    records = module.build_records(count=3)
    actors = module.build_synthetic_actors()
    workflow = module.build_synthetic_workflow(records)
    preview = module.workflow_replacement_preview(records, actors, workflow)

    assert [actor.role for actor in actors] == ["gemologist"] * 4 + ["admin"] * 2
    assert len(workflow) == 9
    assert workflow[0].report_id == "DEMO-00001"
    assert workflow[0].actor_key == "gemologist-01"
    assert module.workflow_checksum(records, actors, workflow) == module.workflow_checksum(records, actors, workflow)
    assert preview["dataset_id"] == "synthetic-demo-v3"
    assert preview["replaces_dataset_id"] == "synthetic-demo-v2"
    assert preview["read_only"] is True


def test_v3_apply_keeps_actors_and_workflow_bound_to_its_manifest(db_session):
    module = load_generator_module()
    records = module.build_records(count=2)
    actors = module.build_synthetic_actors()
    workflow = module.build_synthetic_workflow(records)

    assert module.apply_workflow_dataset(db_session, records, actors, workflow) is True
    assert module.apply_workflow_dataset(db_session, records, actors, workflow) is False
    assert db_session.query(module.models.DemoSyntheticActor).filter_by(dataset_id="synthetic-demo-v3").count() == len(actors)
    assert db_session.query(module.models.DemoWorkflowEvent).filter_by(dataset_id="synthetic-demo-v3").count() == len(workflow)
