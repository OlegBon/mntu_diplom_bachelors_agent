from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_bootstrap_module():
    module_path = PROJECT_ROOT / "scripts" / "bootstrap_mariadb_databases.py"
    spec = spec_from_file_location("bootstrap_mariadb_databases", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_creates_only_named_missing_databases(monkeypatch):
    module = load_bootstrap_module()
    executed_sql = []

    class FakeCursor:
        def execute(self, statement):
            executed_sql.append(statement)

        def close(self):
            pass

    class FakeConnection:
        committed = False
        closed = False

        def cursor(self):
            return FakeCursor()

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()
    monkeypatch.setattr(module, "get_mariadb_connection_options", lambda: {"host": "test"})
    monkeypatch.setattr(module.mysql.connector, "connect", lambda **options: fake_connection)

    module.bootstrap_databases()

    assert executed_sql == [
        "CREATE DATABASE IF NOT EXISTS `diamond_oltp`",
        "CREATE DATABASE IF NOT EXISTS `diamond_market`",
        "CREATE DATABASE IF NOT EXISTS `diamond_analytics`",
    ]
    assert fake_connection.committed is True
    assert fake_connection.closed is True


def test_alembic_demo_dataset_isolation_revision_is_the_only_committed_head():
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    script_directory = ScriptDirectory.from_config(config)

    assert script_directory.get_heads() == ["0014_demo_dataset_isolation"]


def test_demo_dataset_migration_is_schema_only_until_explicit_backfill_approval():
    source = (PROJECT_ROOT / "alembic" / "versions" / "0014_demo_dataset_isolation.py").read_text(encoding="utf-8")

    assert "demo_datasets" in source
    assert "record_scope" in source
    assert "demo_dataset_id" in source
    assert '"uploaded_by_id"' in source
    assert "nullable=True" in source
    assert "op.execute(" not in source
    assert "op.bulk_insert(" not in source


def test_nbu_fx_migration_does_not_backfill_or_reprice_historical_values():
    source = (PROJECT_ROOT / "alembic" / "versions" / "0009_nbu_fx_snapshots.py").read_text(encoding="utf-8")

    assert "fx_data_snapshots" in source
    assert "converted_amount" in source
    assert "UPDATE" not in source
    assert "INSERT INTO diamond_oltp.stone_valuations" not in source


def test_market_reference_policy_migration_changes_only_future_configuration():
    source = (PROJECT_ROOT / "alembic" / "versions" / "0010_market_reference_policy.py").read_text(encoding="utf-8")

    assert "market_reference_policies" in source
    assert "openfacet" in source
    assert "nbu" in source
    assert "stone_valuations" not in source


def test_work_session_migration_adds_empty_operational_tables_without_backfill():
    source = (PROJECT_ROOT / "alembic" / "versions" / "0011_expert_work_sessions.py").read_text(encoding="utf-8")

    assert "report_work_sessions" in source
    assert "report_work_session_events" in source
    assert "report_work_session_leases" in source
    assert "INSERT" not in source
    assert "UPDATE" not in source


def test_wizard_first_save_migration_adds_only_future_timing_fields_and_lease():
    source = (PROJECT_ROOT / "alembic" / "versions" / "0012_wizard_first_save_time.py").read_text(encoding="utf-8")

    assert "wizard_work_sessions" in source
    assert "time_to_first_save_seconds" in source
    assert "INSERT" not in source
    assert "UPDATE" not in source


def test_grading_ruleset_migration_preserves_legacy_reports_without_recalculation():
    migration = PROJECT_ROOT / "alembic" / "versions" / "0007_grading_rulesets.py"
    source = migration.read_text(encoding="utf-8")

    assert "legacy-unversioned-v1" in source
    assert "idc-demo-v1" in source
    assert "calculation_rule_version" in source
    assert "system_cut_grade" not in source
