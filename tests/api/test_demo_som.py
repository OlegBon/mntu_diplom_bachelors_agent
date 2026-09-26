from datetime import datetime
from decimal import Decimal

import pytest

from backend import crud, models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_som_is_artifact_backed_and_admin_only(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    report.system_cut_grade = 0
    db_session.add_all((
        models.StoneValuation(stone_id=report.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal("4100.00"), currency_code="USD", unit="TOTAL_STONE", source_name="Demo Market A", observed_at=datetime(2026, 1, 1)),
        models.StoneValuation(stone_id=report.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal("4200.00"), currency_code="USD", unit="TOTAL_STONE", source_name="Demo Market B", observed_at=datetime(2026, 1, 1)),
    ))
    db_session.commit()
    # A two-row minimum is intentional: add a second isolated report-like fact.
    second_stone = models.Stone(shape="Oval", carat_weight=Decimal("1.50"), color_grade=2, clarity_grade=2, table_percent=Decimal("58"), depth_percent=Decimal("62"), crown_angle=Decimal("35"), pavilion_angle=Decimal("41"), origin="natural", treatment_status="not_assessed", identification_status="preliminary", market_status="not_for_sale")
    db_session.add(second_stone)
    db_session.flush()
    second = models.DiamondReport(report_id="DEMO-00002", record_scope="demo", demo_dataset_id=DATASET_ID, report_date=datetime(2026, 1, 2), shape="Oval", stone_id=second_stone.stone_id, status="issued", system_cut_grade=0)
    db_session.add(second)
    db_session.flush()
    db_session.add_all((
        models.StoneValuation(stone_id=second.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal("4300.00"), currency_code="USD", unit="TOTAL_STONE", source_name="Demo Market A", observed_at=datetime(2026, 1, 2)),
        models.StoneValuation(stone_id=second.stone_id, valuation_kind="synthetic_demo_reference", amount=Decimal("4400.00"), currency_code="USD", unit="TOTAL_STONE", source_name="Demo Market B", observed_at=datetime(2026, 1, 2)),
    ))
    db_session.commit()
    artifact = crud.build_demo_som_artifact(db_session, dataset_id=DATASET_ID)
    db_session.commit()
    assert db_session.query(models.DemoSomAssignment).filter_by(artifact_id=artifact.artifact_id).count() == 2
    headers = auth_headers(client, experts["admin"].username)
    response = client.get(f"/demo/datasets/{DATASET_ID}/som", params={"report_id": "DEMO-00001"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["selected_report"]["selected_provider"] == "Demo Market B"
    assert len(response.json()["cells"]) == 100
    assert client.get(f"/demo/datasets/{DATASET_ID}/som", headers=auth_headers(client, experts["owner"].username)).status_code == 404
