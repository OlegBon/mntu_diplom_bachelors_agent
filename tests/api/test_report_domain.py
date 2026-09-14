import pytest

from tests.conftest import auth_headers


def report_payload(*, confirmed: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "stone": {
            "shape": "Round",
            "carat_weight": 1.0,
            "color_grade": 1,
            "clarity_grade": 1,
            "measurements_length": 6.0,
            "measurements_width": 6.0,
            "measurements_depth": 3.8,
            "table_percent": 58.0,
            "depth_percent": 61.0,
            "crown_angle": 34.5,
            "pavilion_angle": 40.8,
            "polish_grade": 0,
            "symmetry_grade": 0,
            "fluorescence_grade": 0,
            "origin": "natural",
            "treatment_status": "not_assessed",
            "identification_status": "preliminary",
            "market_status": "not_for_sale",
        },
        "expert_comment": "Draft for workflow testing",
    }
    if confirmed:
        payload["expert_proportions_grade"] = 0
        payload["expert_cut_grade"] = 0
    return payload


@pytest.mark.api
@pytest.mark.integration
def test_new_report_domain_is_private_and_creates_a_draft_event(client, experts) -> None:
    assert client.post("/reports", json=report_payload()).status_code == 401

    admin_headers = auth_headers(client, experts["admin"].username)
    assert client.post("/reports", json=report_payload(), headers=admin_headers).status_code == 403

    owner_headers = auth_headers(client, experts["owner"].username)
    created = client.post("/reports", json=report_payload(), headers=owner_headers)

    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "draft"
    assert "price" not in body
    assert body["stone"]["origin"] == "natural"
    assert body["system_cut_grade"] is not None

    report_id = body["report_id"]
    other_headers = auth_headers(client, experts["other"].username)
    assert client.get(f"/reports/{report_id}", headers=other_headers).status_code == 403
    events = client.get(f"/reports/{report_id}/events", headers=owner_headers)
    assert events.status_code == 200
    assert events.json()[0]["action"] == "created"


@pytest.mark.api
@pytest.mark.integration
def test_report_domain_transition_requires_confirmation_and_admin_issuance(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    created = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers)
    assert created.status_code == 200
    report_id = created.json()["report_id"]

    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "review"},
        headers=owner_headers,
    ).status_code == 200
    assert client.put(f"/reports/{report_id}", json=report_payload(confirmed=True), headers=owner_headers).status_code == 422
    issued = client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "issued", "reason": "Reviewed"},
        headers=admin_headers,
    )
    assert issued.status_code == 200
    assert issued.json()["status"] == "issued"
    assert issued.json()["issued_by_id"] == experts["admin"].expert_id

    voided = client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "void", "reason": "Correction required"},
        headers=admin_headers,
    )
    assert voided.status_code == 200
    assert voided.json()["status"] == "void"
