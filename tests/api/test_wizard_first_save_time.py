from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_successful_first_save_claims_server_timed_wizard_lease(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    started = client.post(
        "/report-wizard-sessions",
        json={"tab_id": "tab-0000000000001"},
        headers=owner_headers,
    )
    assert started.status_code == 200
    wizard_session_id = started.json()["wizard_session_id"]
    lease = db_session.get(models.WizardWorkSession, wizard_session_id)
    lease.started_at = datetime.now(timezone.utc) - timedelta(seconds=75)
    db_session.commit()

    response = client.post(
        "/reports",
        json={**report_payload(), "wizard_session_id": wizard_session_id},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert 70 <= response.json()["time_to_first_save_seconds"] <= 80
    assert response.json()["first_save_started_at"] is not None
    assert db_session.query(models.WizardWorkSession).count() == 0


@pytest.mark.api
@pytest.mark.integration
def test_replaced_or_offline_wizard_lease_does_not_block_unmeasured_report_creation(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    first = client.post("/report-wizard-sessions", json={"tab_id": "tab-0000000000001"}, headers=owner_headers)
    second = client.post("/report-wizard-sessions", json={"tab_id": "tab-0000000000002"}, headers=owner_headers)
    assert first.status_code == second.status_code == 200
    assert first.json()["wizard_session_id"] != second.json()["wizard_session_id"]
    assert db_session.query(models.WizardWorkSession).count() == 1

    stale_response = client.post(
        "/reports",
        json={**report_payload(), "wizard_session_id": first.json()["wizard_session_id"]},
        headers=owner_headers,
    )
    offline_response = client.post("/reports", json=report_payload(), headers=owner_headers)

    assert stale_response.status_code == offline_response.status_code == 200
    assert stale_response.json()["time_to_first_save_seconds"] is None
    assert offline_response.json()["time_to_first_save_seconds"] is None


@pytest.mark.api
@pytest.mark.integration
def test_wizard_timing_is_gemologist_only_and_expert_statistics_keep_it_separate(client, experts, db_session) -> None:
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)
    assert client.post("/report-wizard-sessions", json={"tab_id": "tab-0000000000001"}, headers=admin_headers).status_code == 403

    session_id = client.post("/report-wizard-sessions", json={"tab_id": "tab-0000000000001"}, headers=owner_headers).json()["wizard_session_id"]
    lease = db_session.get(models.WizardWorkSession, session_id)
    lease.started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    db_session.commit()
    assert client.post("/reports", json={**report_payload(), "wizard_session_id": session_id}, headers=owner_headers).status_code == 200

    rows = client.get("/statistics/expert-performance", headers=admin_headers).json()
    owner = next(row for row in rows if row["expert_username"] == experts["owner"].username)
    assert owner["completed_first_save_timings"] == 1
    assert 115 <= owner["total_time_to_first_save_seconds"] <= 125
    assert owner["completed_work_sessions"] == 0
