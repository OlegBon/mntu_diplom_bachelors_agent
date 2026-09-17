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


def test_alembic_grading_rulesets_revision_is_the_only_committed_head():
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    script_directory = ScriptDirectory.from_config(config)

    assert script_directory.get_heads() == ["0007_grading_rulesets"]


def test_grading_ruleset_migration_preserves_legacy_reports_without_recalculation():
    migration = PROJECT_ROOT / "alembic" / "versions" / "0007_grading_rulesets.py"
    source = migration.read_text(encoding="utf-8")

    assert "legacy-unversioned-v1" in source
    assert "idc-demo-v1" in source
    assert "calculation_rule_version" in source
    assert "system_cut_grade" not in source
