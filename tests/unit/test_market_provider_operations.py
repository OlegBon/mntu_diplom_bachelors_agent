from datetime import datetime, timedelta, timezone

from backend.market_operations import freshness_status


def test_freshness_status_uses_warning_and_block_thresholds() -> None:
    now = datetime(2026, 9, 24, 12, tzinfo=timezone.utc)

    assert freshness_status(
        latest_retrieved_at=None, warn_after_hours=24, block_after_hours=72, now=now,
    ) == "missing"
    assert freshness_status(
        latest_retrieved_at=now - timedelta(hours=23), warn_after_hours=24, block_after_hours=72, now=now,
    ) == "fresh"
    assert freshness_status(
        latest_retrieved_at=now - timedelta(hours=25), warn_after_hours=24, block_after_hours=72, now=now,
    ) == "warning"
    assert freshness_status(
        latest_retrieved_at=now - timedelta(hours=73), warn_after_hours=24, block_after_hours=72, now=now,
    ) == "stale"


def test_market_provider_operations_migration_is_future_only() -> None:
    from pathlib import Path

    migration = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "0013_market_provider_operations.py"
    source = migration.read_text(encoding="utf-8")

    assert "market_provider_schedules" in source
    assert "market_provider_operations" in source
    assert "UPDATE" not in source
    assert "stone_valuations" not in source
