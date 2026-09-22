import pytest
from datetime import datetime, timedelta, timezone

from backend import models
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers, create_expert


@pytest.mark.api
@pytest.mark.integration
def test_expert_statistics_is_admin_only_and_reports_operational_aggregates(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    empty_expert = create_expert(db_session, username="empty-expert")

    assert client.get("/statistics/expert-performance").status_code == 401
    assert client.get("/statistics/expert-performance", headers=owner_headers).status_code == 403

    first = report_payload()
    second = report_payload()
    first_report_id = client.post("/reports", json=first, headers=owner_headers).json()["report_id"]
    second_report_id = client.post("/reports", json=second, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{first_report_id}/transitions",
        json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{first_report_id}/transitions",
        json={"target_status": "issued", "reason": None}, headers=admin_headers,
    ).status_code == 422

    confirmed = report_payload(confirmed=True)
    issued_report_id = client.post("/reports", json=confirmed, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{issued_report_id}/transitions",
        json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{issued_report_id}/transitions",
        json={"target_status": "issued", "reason": None}, headers=admin_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{issued_report_id}/transitions",
        json={"target_status": "void", "reason": None}, headers=admin_headers,
    ).status_code == 200

    response = client.get("/statistics/expert-performance", headers=admin_headers)
    assert response.status_code == 200
    rows = {row["expert_username"]: row for row in response.json()}
    owner = rows[experts["owner"].username]
    assert owner["total_reports"] == 3
    assert owner["draft_reports"] == 1
    assert owner["review_reports"] == 1
    assert owner["issued_reports"] == 0
    assert owner["void_reports"] == 1
    assert "avg_carat_weight" not in owner
    assert owner["is_active"] is True
    assert rows[empty_expert.username]["total_reports"] == 0


@pytest.mark.api
@pytest.mark.integration
def test_admin_review_statistics_tracks_review_cycles_not_active_work_time(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    payload = report_payload(confirmed=True)
    report_id = client.post("/reports", json=payload, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "issued", "reason": None}, headers=admin_headers,
    ).status_code == 200

    assert client.get("/statistics/admin-review-performance").status_code == 401
    assert client.get("/statistics/admin-review-performance", headers=owner_headers).status_code == 403
    response = client.get("/statistics/admin-review-performance", headers=admin_headers)
    assert response.status_code == 200
    admin = response.json()["admins"][0]
    assert admin["admin_id"] == experts["admin"].expert_id
    assert admin["completed_reviews"] == 1
    assert admin["issued_reports"] == 1
    assert admin["shortest_reviews"][0]["report_id"] == report_id
    assert admin["longest_reviews"][0]["decision"] == "issued"
    assert response.json()["pending_review_count"] == 0


@pytest.mark.api
@pytest.mark.integration
def test_work_sessions_are_owner_only_single_tab_and_finish_on_review(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    report_id = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers).json()["report_id"]
    first_tab = "tab-0000000000001"
    second_tab = "tab-0000000000002"

    assert client.post(
        f"/reports/{report_id}/work-session", json={"action": "start", "tab_id": first_tab}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/work-session", json={"action": "heartbeat", "tab_id": first_tab}, headers=admin_headers,
    ).status_code == 409

    session = db_session.query(models.ReportWorkSession).one()
    lease = db_session.query(models.ReportWorkSessionLease).one()
    session.last_activity_at = datetime.now(timezone.utc) - timedelta(seconds=20)
    lease.expires_at = datetime.now(timezone.utc) + timedelta(seconds=60)
    db_session.commit()
    heartbeat = client.post(
        f"/reports/{report_id}/work-session", json={"action": "heartbeat", "tab_id": first_tab}, headers=owner_headers,
    )
    assert heartbeat.status_code == 200
    assert 1 <= heartbeat.json()["active_seconds"] <= 60

    replacement = client.post(
        f"/reports/{report_id}/work-session", json={"action": "resume", "tab_id": second_tab}, headers=owner_headers,
    )
    assert replacement.status_code == 200
    assert client.post(
        f"/reports/{report_id}/work-session", json={"action": "heartbeat", "tab_id": first_tab}, headers=owner_headers,
    ).status_code == 409
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200

    sessions = db_session.query(models.ReportWorkSession).order_by(models.ReportWorkSession.started_at).all()
    assert len(sessions) == 2
    assert sessions[0].ended_at is not None
    assert sessions[0].end_reason == "replaced"
    assert sessions[1].ended_at is not None
    assert sessions[1].end_reason == "finish"
    assert db_session.query(models.ReportWorkSessionLease).count() == 0
    actions = [event.action for event in db_session.query(models.ReportWorkSessionEvent).all()]
    assert actions == ["start", "heartbeat", "pause", "resume", "finish"]


@pytest.mark.api
@pytest.mark.integration
def test_expert_statistics_filter_uses_report_creation_and_finished_sessions(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    report_id = client.post("/reports", json=report_payload(), headers=owner_headers).json()["report_id"]
    finished_at = datetime.now(timezone.utc)
    db_session.add(models.ReportWorkSession(
        work_session_id="11111111-1111-1111-1111-111111111111", report_id=report_id,
        expert_id=experts["owner"].expert_id, tab_id="tab-0000000000003",
        started_at=finished_at - timedelta(minutes=3), last_activity_at=finished_at - timedelta(minutes=1),
        ended_at=finished_at, active_seconds=120, end_reason="pause",
    ))
    db_session.commit()

    selected_date = finished_at.date().isoformat()
    response = client.get(
        f"/statistics/expert-performance?date_from={selected_date}&date_to={selected_date}", headers=admin_headers,
    )
    assert response.status_code == 200
    owner = {row["expert_username"]: row for row in response.json()}[experts["owner"].username]
    assert owner["total_reports"] == 1
    assert owner["completed_work_sessions"] == 1
    assert owner["total_active_seconds"] == 120
    assert owner["shortest_work_sessions"][0]["report_id"] == report_id
    assert owner["longest_work_sessions"][0]["duration_seconds"] == 120
    assert client.get(
        "/statistics/expert-performance?date_from=2026-09-20&date_to=2026-09-19", headers=admin_headers,
    ).status_code == 422
