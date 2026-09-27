from datetime import datetime
from decimal import Decimal

import pytest

from backend import crud, models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report


@pytest.mark.api
@pytest.mark.integration
def test_demo_som_uses_newest_eligible_report_as_initial_example(db_session, experts) -> None:
    first = create_demo_report(db_session, experts)
    first.system_cut_grade = 0
    second_stone = models.Stone(
        shape="Oval", carat_weight=Decimal("1.50"), color_grade=2,
        clarity_grade=2, table_percent=Decimal("58"), depth_percent=Decimal("62"),
        crown_angle=Decimal("35"), pavilion_angle=Decimal("41"), origin="natural",
        treatment_status="not_assessed", identification_status="preliminary",
        market_status="not_for_sale",
    )
    db_session.add(second_stone)
    db_session.flush()
    second = models.DiamondReport(
        report_id="DEMO-00002", record_scope="demo", demo_dataset_id=DATASET_ID,
        report_date=datetime(2026, 1, 2), shape="Oval", stone_id=second_stone.stone_id,
        status="issued", system_cut_grade=0,
    )
    db_session.add(second)
    db_session.flush()
    for report, amount in ((first, Decimal("4100")), (second, Decimal("4400"))):
        db_session.add(models.StoneValuation(
            stone_id=report.stone_id, valuation_kind="synthetic_demo_reference",
            amount=amount, currency_code="USD", unit="TOTAL_STONE",
            source_name="Demo Market B", observed_at=datetime(2026, 1, 2),
        ))
    db_session.commit()
    crud.build_demo_som_artifact(db_session, dataset_id=DATASET_ID)
    db_session.commit()

    response = crud.get_demo_som(db_session, dataset_id=DATASET_ID, report_id=None)

    assert response.selected_report is not None
    assert response.selected_report.report_id == "DEMO-00002"
    assert response.selected_report.is_initial_example is True
    assert response.map_overview.occupied_cells == 2
    assert response.map_overview.provider_usage == {"Demo Market A": 0, "Demo Market B": 2}
