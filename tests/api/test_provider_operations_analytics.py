from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from backend import models
from tests.conftest import auth_headers


def _report(*, report_id: str, stone: models.Stone, created_at: datetime) -> models.DiamondReport:
    return models.DiamondReport(
        report_id=report_id,
        record_scope="operational",
        report_date=created_at,
        created_at=created_at,
        updated_at=created_at,
        status="draft",
        shape=stone.shape,
        stone_id=stone.stone_id,
    )


@pytest.mark.api
@pytest.mark.integration
def test_provider_operations_analytics_is_admin_only_and_scope_bound(client, db_session, experts) -> None:
    now = datetime.now(timezone.utc)
    covered_stone = models.Stone(shape="Round", carat_weight=Decimal("1.00"), color_grade=0, clarity_grade=0, origin="natural")
    excluded_stone = models.Stone(shape="Oval", carat_weight=Decimal("1.10"), color_grade=1, clarity_grade=1, origin="lab_grown")
    incomplete_stone = models.Stone(shape="Pear", carat_weight=None, color_grade=None, clarity_grade=None, origin="natural")
    demo_stone = models.Stone(shape="Round", carat_weight=Decimal("1.00"), color_grade=0, clarity_grade=0, origin="natural")
    db_session.add_all([covered_stone, excluded_stone, incomplete_stone, demo_stone])
    db_session.commit()
    db_session.add_all([
        _report(report_id="DR-COVERED", stone=covered_stone, created_at=now),
        _report(report_id="DR-EXCLUDED", stone=excluded_stone, created_at=now),
        _report(report_id="DR-INCOMPLETE", stone=incomplete_stone, created_at=now),
        models.DiamondReport(report_id="DEMO-IGNORE", record_scope="demo", demo_dataset_id="demo-test", report_date=now, updated_at=now, status="draft", shape="Round", stone_id=demo_stone.stone_id),
        models.MarketDataProvider(provider_code="openfacet", display_name="OpenFacet", provider_type="market_reference", documentation_url="https://example.test/docs", terms_url="https://example.test/terms", scope_note="Natural comparable reference.", is_active=True),
        models.MarketProviderSchedule(provider_code="openfacet", enabled=True, timezone_name="Europe/Kyiv", scheduled_hour=8, scheduled_minute=0, warn_after_hours=1, block_after_hours=2),
        models.MarketDataSnapshot(provider_code="openfacet", snapshot_kind="market_reference", status="approved", currency_code="USD", unit="USD_PER_CARAT", source_url="https://example.test/data", methodology_url="https://example.test/method", coverage_note="Natural only.", quote_count=1, content_sha256="a" * 64, retrieved_at=now - timedelta(days=2), approved_at=now - timedelta(days=2)),
    ])
    db_session.commit()
    snapshot = db_session.query(models.MarketDataSnapshot).one()
    db_session.add_all([
        models.StoneValuation(stone_id=covered_stone.stone_id, valuation_kind="system_market_reference", amount=Decimal("5000.00"), currency_code="USD", unit="TOTAL", source_name="OpenFacet", market_snapshot_id=snapshot.snapshot_id, observed_at=now),
        models.MarketProviderOperation(provider_code="openfacet", trigger_type="scheduled", status="failed", attempt_number=2, started_at=now, completed_at=now, message="Temporary failure"),
    ])
    db_session.commit()

    admin_headers = auth_headers(client, experts["admin"].username)
    response = client.get("/statistics/provider-operations", headers=admin_headers)
    assert response.status_code == 200
    row = response.json()["providers"][0]
    assert row["provider_code"] == "openfacet"
    assert row["freshness_status"] == "stale"
    assert row["snapshots_approved"] == 1
    assert row["failed_operations"] == 1
    assert row["retry_operations"] == 1
    assert row["coverage"] == {
        "candidate_draft_reports": 3,
        "covered_draft_reports": 1,
        "excluded_non_natural_reports": 1,
        "missing_characteristics_reports": 1,
        "snapshot_unavailable_reports": 1,
        "quote_not_covered_reports": 0,
        "covered_report_ids": ["DR-COVERED"],
    }
    assert client.get("/statistics/provider-operations", headers=auth_headers(client, experts["owner"].username)).status_code == 403
    assert client.get("/statistics/provider-operations?date_from=2026-09-29&date_to=2026-09-28", headers=admin_headers).status_code == 422
