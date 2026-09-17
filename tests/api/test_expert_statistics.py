import pytest

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
    first["stone"]["carat_weight"] = 1.0
    second = report_payload()
    second["stone"]["carat_weight"] = 2.0
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
    confirmed["stone"]["carat_weight"] = 3.0
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
    assert owner["avg_carat_weight"] == 2.0
    assert owner["is_active"] is True
    assert rows[empty_expert.username]["total_reports"] == 0
    assert rows[empty_expert.username]["avg_carat_weight"] is None
