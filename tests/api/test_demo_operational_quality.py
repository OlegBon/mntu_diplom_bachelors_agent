from datetime import datetime

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_operational_quality_is_dataset_bound_and_admin_only(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    actor = models.DemoSyntheticActor(dataset_id=DATASET_ID, actor_key="gem-01", role="gemologist", display_name="Demo Gemologist", sort_order=1)
    db_session.add(actor)
    db_session.flush()
    db_session.add(models.DemoWorkflowEvent(
        dataset_id=DATASET_ID, report_id=report.report_id, actor_id=actor.actor_id,
        action="draft_completed", occurred_at=datetime(2026, 1, 1, 13), duration_seconds=120,
    ))
    db_session.commit()

    admin_headers = auth_headers(client, experts["admin"].username)
    response = client.get(
        f"/demo/datasets/{DATASET_ID}/operational-quality",
        params={"date_from": "2026-01-01", "date_to": "2026-01-01"}, headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "demo"
    assert body["report_cohort_count"] == 1
    assert body["workflow_created_count"] == 1
    assert body["delivery_is_modeled"] is False
    assert body["reports_with_media_count"] == 0
    assert client.get(
        f"/demo/datasets/{DATASET_ID}/operational-quality", headers=auth_headers(client, experts["owner"].username),
    ).status_code == 404
