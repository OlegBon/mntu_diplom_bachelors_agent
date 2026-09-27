from datetime import datetime
from decimal import Decimal

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_provider_analytics_is_scope_bound_date_scoped_and_admin_only(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    dataset = db_session.get(models.DemoDataset, DATASET_ID)
    assert dataset is not None
    dataset.analysis_eligibility = '["demo_operations", "synthetic_som", "demo_provider_analytics"]'
    db_session.add_all((
        models.StoneValuation(
            stone_id=report.stone_id,
            valuation_kind="synthetic_demo_reference",
            amount=Decimal("1000.00"),
            currency_code="USD",
            unit="TOTAL_STONE",
            source_name="Demo Market A",
            source_reference="test/a",
            observed_at=datetime(2026, 1, 1, 12),
        ),
        models.StoneValuation(
            stone_id=report.stone_id,
            valuation_kind="synthetic_demo_reference",
            amount=Decimal("1100.00"),
            currency_code="USD",
            unit="TOTAL_STONE",
            source_name="Demo Market B",
            source_reference="test/b",
            observed_at=datetime(2026, 1, 1, 12),
        ),
    ))
    operational_stone = models.Stone(shape="Round", carat_weight=Decimal("1.00"))
    db_session.add(operational_stone)
    db_session.flush()
    db_session.add_all((
        models.DiamondReport(
            report_id="DR-99991",
            record_scope="operational",
            report_date=datetime(2026, 1, 1, 12),
            stone_id=operational_stone.stone_id,
            status="issued",
            shape="Round",
        ),
        models.StoneValuation(
            stone_id=operational_stone.stone_id,
            valuation_kind="synthetic_demo_reference",
            amount=Decimal("999999.00"),
            currency_code="USD",
            unit="TOTAL_STONE",
            source_name="Demo Market A",
            source_reference="must-not-leak",
            observed_at=datetime(2026, 1, 1, 12),
        ),
    ))
    db_session.commit()

    admin_headers = auth_headers(client, experts["admin"].username)
    response = client.get(
        f"/demo/datasets/{DATASET_ID}/provider-analytics",
        params={"date_from": "2026-01-01", "date_to": "2026-01-01"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "synthetic_demo"
    assert payload["candidate_report_count"] == 1
    assert payload["reference_count"] == 2
    assert payload["providers"] == [
        {
            "provider_name": "Demo Market A",
            "reference_count": 1,
            "covered_report_count": 1,
            "first_observed_at": "2026-01-01T12:00:00",
            "last_observed_at": "2026-01-01T12:00:00",
            "min_amount": "1000.00",
            "median_amount": "1000.00",
            "max_amount": "1000.00",
            "latest_report_id": "DEMO-00001",
            "source_class": "Fictional synthetic provider",
            "provenance": "synthetic-demo-vN / deterministic generator",
            "terms_status": "Not a contract or market-data agreement",
            "usage_policy": "Allowed only as an isolated synthetic demonstration reference.",
        },
        {
            "provider_name": "Demo Market B",
            "reference_count": 1,
            "covered_report_count": 1,
            "first_observed_at": "2026-01-01T12:00:00",
            "last_observed_at": "2026-01-01T12:00:00",
            "min_amount": "1100.00",
            "median_amount": "1100.00",
            "max_amount": "1100.00",
            "latest_report_id": "DEMO-00001",
            "source_class": "Fictional synthetic provider",
            "provenance": "synthetic-demo-vN / deterministic generator",
            "terms_status": "Not a contract or market-data agreement",
            "usage_policy": "Allowed only as an isolated synthetic demonstration reference.",
        },
    ]
    assert client.get(f"/demo/datasets/{DATASET_ID}/provider-analytics", headers=auth_headers(client, experts["owner"].username)).status_code == 404


@pytest.mark.api
@pytest.mark.integration
def test_demo_provider_analytics_rejects_a_manifest_without_its_explicit_scenario(client, db_session, experts) -> None:
    create_demo_report(db_session, experts)

    response = client.get(
        f"/demo/datasets/{DATASET_ID}/provider-analytics",
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 404
