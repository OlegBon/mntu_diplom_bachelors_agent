from datetime import datetime

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_workflow_analytics_exposes_only_synthetic_duration_examples(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    actor = models.DemoSyntheticActor(
        dataset_id=DATASET_ID,
        actor_key="gem-01",
        role="gemologist",
        display_name="Demo Gemologist 01",
        sort_order=1,
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add_all((
        models.DemoWorkflowEvent(
            dataset_id=DATASET_ID,
            report_id=report.report_id,
            actor_id=actor.actor_id,
            action="draft_completed",
            occurred_at=datetime(2026, 1, 3, 10),
            duration_seconds=300,
        ),
        models.DemoWorkflowEvent(
            dataset_id=DATASET_ID,
            report_id=report.report_id,
            actor_id=actor.actor_id,
            action="draft_completed",
            occurred_at=datetime(2026, 1, 4, 10),
            duration_seconds=120,
        ),
    ))
    db_session.commit()

    response = client.get(
        f"/demo/datasets/{DATASET_ID}/workflow-analytics",
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 200
    stats = response.json()["experts"][0]
    assert stats["median_duration_seconds"] == 210
    assert stats["shortest_intervals"][0]["duration_seconds"] == 120
    assert stats["longest_intervals"][0]["duration_seconds"] == 300
    assert stats["shortest_intervals"][0]["report_id"].startswith("DEMO-")
