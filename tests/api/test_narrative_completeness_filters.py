from datetime import datetime, timezone

import pytest

from backend import models
from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_operational_report_list_filters_empty_current_text_and_date_scoped_transition_reason(client, db_session, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    current_empty = report_payload(confirmed=True)
    current_empty["stone"]["identification_method"] = "  \t"
    current_empty["stone"]["identification_conclusion"] = "Заповнено"
    current_empty["expert_comment"] = "Заповнено"
    current_id = client.post("/reports", json=current_empty, headers=owner_headers).json()["report_id"]

    event_empty = report_payload(confirmed=True)
    event_empty["stone"]["identification_method"] = "Метод"
    event_empty["stone"]["identification_conclusion"] = "Висновок"
    event_empty["expert_comment"] = "Коментар"
    event_id = client.post("/reports", json=event_empty, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{event_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    db_session.query(models.ReportEvent).filter(
        models.ReportEvent.report_id == event_id, models.ReportEvent.action == "status_changed",
    ).update({"created_at": datetime(2025, 2, 3, tzinfo=timezone.utc)})
    db_session.query(models.DiamondReport).filter(
        models.DiamondReport.report_id == event_id,
    ).update({"report_date": datetime(2025, 2, 3, tzinfo=timezone.utc)})

    event_filled = report_payload(confirmed=True)
    event_filled["stone"]["identification_method"] = "Метод"
    event_filled["stone"]["identification_conclusion"] = "Висновок"
    event_filled["expert_comment"] = "Коментар"
    event_filled_id = client.post("/reports", json=event_filled, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{event_filled_id}/transitions", json={"target_status": "review", "reason": "Перевірено"}, headers=owner_headers,
    ).status_code == 200
    db_session.query(models.ReportEvent).filter(
        models.ReportEvent.report_id == event_filled_id, models.ReportEvent.action == "status_changed",
    ).update({"created_at": datetime(2025, 2, 3, tzinfo=timezone.utc)})
    db_session.query(models.DiamondReport).filter(
        models.DiamondReport.report_id == event_filled_id,
    ).update({"report_date": datetime(2025, 2, 3, tzinfo=timezone.utc)})
    db_session.commit()

    method = client.get("/reports", params=[("empty_narrative", "identification_method")], headers=owner_headers)
    assert method.status_code == 200
    assert [item["report_id"] for item in method.json()["items"]] == [current_id]

    event = client.get(
        "/reports", params=[("empty_narrative", "status_transition_reason"), ("date_from", "2025-02-03"), ("date_to", "2025-02-03")], headers=owner_headers,
    )
    assert event.status_code == 200
    assert [item["report_id"] for item in event.json()["items"]] == [event_id]

    filled_event = client.get(
        "/reports",
        params=[
            ("empty_narrative", "status_transition_reason"), ("narrative_presence", "filled"),
            ("date_from", "2025-02-03"), ("date_to", "2025-02-03"),
        ],
        headers=owner_headers,
    )
    assert filled_event.status_code == 200
    assert [item["report_id"] for item in filled_event.json()["items"]] == [event_filled_id]

    filled_method = client.get(
        "/reports",
        params=[("empty_narrative", "identification_method"), ("narrative_presence", "filled")],
        headers=admin_headers,
    )
    assert {item["report_id"] for item in filled_method.json()["items"]} == {event_id, event_filled_id}

    assert client.get(
        "/reports", params={"narrative_presence": "unknown"}, headers=owner_headers,
    ).status_code == 422

    combined = client.get(
        "/reports", params=[("empty_narrative", "identification_method"), ("empty_narrative", "status_transition_reason")], headers=admin_headers,
    )
    assert {item["report_id"] for item in combined.json()["items"]} == {current_id, event_id}


@pytest.mark.api
@pytest.mark.integration
def test_demo_report_list_is_dataset_bound_and_does_not_reinterpret_missing_event_comments(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    report.stone.identification_method = " \n "
    db_session.commit()
    admin_headers = auth_headers(client, experts["admin"].username)

    response = client.get(
        f"/demo/datasets/{DATASET_ID}/reports", params=[("empty_narrative", "identification_method")], headers=admin_headers,
    )
    assert response.status_code == 200
    assert [item["report_id"] for item in response.json()["items"]] == [report.report_id]
    event_only = client.get(
        f"/demo/datasets/{DATASET_ID}/reports", params=[("empty_narrative", "status_transition_reason")], headers=admin_headers,
    )
    assert event_only.status_code == 200
    assert event_only.json()["total"] == 0
    filled = client.get(
        f"/demo/datasets/{DATASET_ID}/reports",
        params=[("empty_narrative", "identification_method"), ("narrative_presence", "filled")], headers=admin_headers,
    )
    assert filled.status_code == 200
    assert filled.json()["total"] == 0
    assert client.get(
        f"/demo/datasets/{DATASET_ID}/reports", params=[("empty_narrative", "identification_method")], headers=auth_headers(client, experts["owner"].username),
    ).status_code == 404
