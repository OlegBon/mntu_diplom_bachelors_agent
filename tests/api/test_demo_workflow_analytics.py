from datetime import datetime

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_workflow_analytics_is_admin_only_and_date_scoped(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    gemologist = models.DemoSyntheticActor(dataset_id=DATASET_ID, actor_key="gem-01", role="gemologist", display_name="Demo Gemologist 01", sort_order=1)
    administrator = models.DemoSyntheticActor(dataset_id=DATASET_ID, actor_key="admin-01", role="admin", display_name="Demo Administrator 01", sort_order=1)
    db_session.add_all((gemologist, administrator))
    db_session.flush()
    db_session.add_all((
        models.DemoWorkflowEvent(dataset_id=DATASET_ID, report_id=report.report_id, actor_id=gemologist.actor_id, action="draft_completed", occurred_at=datetime(2026, 1, 3, 10), duration_seconds=300),
        models.DemoWorkflowEvent(dataset_id=DATASET_ID, report_id=report.report_id, actor_id=administrator.actor_id, action="review_completed", occurred_at=datetime(2026, 1, 4, 10), duration_seconds=120),
    ))
    db_session.commit()
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)

    response = client.get(f"/demo/datasets/{DATASET_ID}/workflow-analytics", params={"date_from": "2026-01-03", "date_to": "2026-01-03"}, headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["experts"][0]["total_duration_seconds"] == 300
    assert response.json()["administrators"][0]["reports_touched"] == 0
    assert client.get(f"/demo/datasets/{DATASET_ID}/workflow-analytics", headers=owner_headers).status_code == 404
