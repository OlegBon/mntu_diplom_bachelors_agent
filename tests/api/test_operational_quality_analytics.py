import pytest

from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_operational_quality_analytics_describes_coverage_and_workflow_without_text(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    payload = report_payload(confirmed=True)
    payload["stone"]["identification_method"] = "Лупа та мікроскоп"
    report_id = client.post("/reports", json=payload, headers=owner_headers).json()["report_id"]

    assert client.get("/statistics/operational-quality").status_code == 401
    assert client.get("/statistics/operational-quality", headers=owner_headers).status_code == 403
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "draft", "reason": "Потрібне уточнення"}, headers=admin_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "issued", "reason": "Перевірено"}, headers=admin_headers,
    ).status_code == 200

    response = client.get("/statistics/operational-quality", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["report_cohort_count"] == 1
    assert body["current_status_counts"]["issued"] == 1
    assert body["workflow_created_count"] == 1
    assert body["workflow_sent_to_review_count"] == 2
    assert body["workflow_returned_to_draft_count"] == 1
    assert body["workflow_issued_count"] == 1
    assert body["issued_without_active_passport_count"] == 1
    required = {row["key"]: row for row in body["required_field_coverage"]}
    optional = {row["key"]: row for row in body["optional_field_coverage"]}
    assert required["geometry"]["filled_count"] == 1
    assert optional["identification_method"]["filled_count"] == 1
    assert optional["identification_conclusion"]["missing_count"] == 1
    assert "text" not in str(body).lower()

