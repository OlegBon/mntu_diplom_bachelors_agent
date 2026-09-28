from datetime import datetime

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_narrative_analytics_is_dataset_bound_date_scoped_and_admin_only(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    report.expert_comment = "Synthetic коментар для перевірки"
    report.stone.identification_method = "Synthetic метод"
    report.stone.identification_conclusion = "Synthetic висновок"
    operational_stone = models.Stone(shape="Round", carat_weight=1)
    db_session.add(operational_stone)
    db_session.flush()
    db_session.add(models.DiamondReport(
        report_id="DR-IGNORE", record_scope="operational", report_date=datetime(2026, 1, 1, 12),
        stone_id=operational_stone.stone_id, status="draft", shape="Round", expert_comment="Не має потрапити",
    ))
    db_session.commit()

    admin_headers = auth_headers(client, experts["admin"].username)
    response = client.get(
        f"/demo/datasets/{DATASET_ID}/narrative-quality",
        params={"date_from": "2026-01-01", "date_to": "2026-01-01"}, headers=admin_headers,
    )
    assert response.status_code == 200
    fields = {field["field_key"]: field for field in response.json()["fields"]}
    assert fields["identification_method"]["non_empty_count"] == 1
    assert fields["identification_method"]["shortest"][0]["report_id"] == report.report_id
    assert fields["expert_comment"]["non_empty_count"] == 1
    assert fields["status_transition_reason"]["non_empty_count"] == 0
    assert "synthetic" in fields["expert_comment"]["source_semantics"].casefold()
    assert client.get(
        f"/demo/datasets/{DATASET_ID}/narrative-quality", headers=auth_headers(client, experts["owner"].username),
    ).status_code == 404
