import pytest

from tests.conftest import auth_headers


def report_payload(*, confirmed: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "examination_date": "2026-09-15",
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
    assert body["examination_date"] == "2026-09-15"
    assert body["price"] is None
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
def test_report_wizard_preview_uses_server_contract_and_does_not_reserve_id(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)

    assert client.get("/reports/next-id").status_code == 401
    assert client.get("/reports/next-id", headers=admin_headers).status_code == 403
    assert client.post("/reports/preview", json=report_payload()["stone"]).status_code == 401
    assert client.post("/reports/preview", json=report_payload()["stone"], headers=admin_headers).status_code == 403

    first_preview = client.get("/reports/next-id", headers=owner_headers)
    assert first_preview.status_code == 200
    assert first_preview.json()["report_id"] == "DR-00001"

    calculation = client.post("/reports/preview", json=report_payload()["stone"], headers=owner_headers)
    assert calculation.status_code == 200
    calculation_body = calculation.json()
    assert calculation_body["system_proportions_grade"] == 0
    assert calculation_body["system_cut_grade"] == 0
    assert calculation_body["calculation_rule_version"] == "idc-demo-v1"
    assert calculation_body["demo_price_usd"] is None

    created = client.post("/reports", json=report_payload(), headers=owner_headers)
    assert created.status_code == 200
    assert created.json()["report_id"] == "DR-00001"
    assert client.get("/reports/next-id", headers=owner_headers).json()["report_id"] == "DR-00002"


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


@pytest.mark.api
@pytest.mark.integration
def test_expert_final_cut_is_server_derived_and_client_override_is_ignored(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    payload = report_payload(confirmed=True)
    payload["expert_proportions_grade"] = 2
    payload["expert_cut_grade"] = 0
    payload["stone"]["polish_grade"] = 0
    payload["stone"]["symmetry_grade"] = 1

    created = client.post("/reports", json=payload, headers=owner_headers)

    assert created.status_code == 200
    assert created.json()["expert_proportions_grade"] == 2
    assert created.json()["expert_cut_grade"] == 2
    assert created.json()["expert_confirmed_at"] is not None


@pytest.mark.api
@pytest.mark.integration
def test_draft_update_records_an_auditable_event_and_preserves_owner_rbac(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    other_headers = auth_headers(client, experts["other"].username)
    created = client.post("/reports", json=report_payload(), headers=owner_headers)
    assert created.status_code == 200
    report_id = created.json()["report_id"]

    changed_payload = report_payload(confirmed=True)
    changed_payload["expert_comment"] = "Updated expert observation"
    changed_payload["stone"]["market_status"] = "available"

    assert client.put(f"/reports/{report_id}", json=changed_payload, headers=other_headers).status_code == 403
    updated = client.put(f"/reports/{report_id}", json=changed_payload, headers=owner_headers)
    assert updated.status_code == 200
    assert updated.json()["stone"]["market_status"] == "available"
    assert updated.json()["expert_cut_grade"] == 0

    events = client.get(f"/reports/{report_id}/events", headers=owner_headers)
    assert events.status_code == 200
    assert [(event["action"], event["from_status"], event["to_status"]) for event in events.json()] == [
        ("created", None, "draft"),
        ("report_updated", "draft", "draft"),
    ]


@pytest.mark.api
@pytest.mark.integration
def test_report_dashboard_list_paginates_searches_filters_and_scopes_visibility(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    other_headers = auth_headers(client, experts["other"].username)
    admin_headers = auth_headers(client, experts["admin"].username)

    first_payload = report_payload()
    first_payload["stone"].update({"market_status": "available", "shape": "Oval", "color_grade": 2, "clarity_grade": 3})
    first = client.post("/reports", json=first_payload, headers=owner_headers)
    assert first.status_code == 200

    second_payload = report_payload()
    second_payload["stone"].update({"market_status": "sold", "shape": "Round", "color_grade": 1, "clarity_grade": 1})
    second = client.post("/reports", json=second_payload, headers=owner_headers)
    assert second.status_code == 200

    other = client.post("/reports", json=report_payload(), headers=other_headers)
    assert other.status_code == 200

    owner_page = client.get("/reports?page=1&page_size=1", headers=owner_headers)
    assert owner_page.status_code == 200
    owner_body = owner_page.json()
    assert owner_body["total"] == 2
    assert owner_body["page"] == 1
    assert owner_body["page_size"] == 1
    assert owner_body["total_pages"] == 2
    assert len(owner_body["items"]) == 1

    sold = client.get("/reports?market_status=sold", headers=owner_headers)
    assert sold.status_code == 200
    assert sold.json()["total"] == 1
    assert sold.json()["items"][0]["report_id"] == second.json()["report_id"]

    sale_filter = client.get("/reports?sold=true", headers=owner_headers)
    assert sale_filter.status_code == 200
    assert sale_filter.json()["total"] == 1
    assert sale_filter.json()["items"][0]["report_id"] == second.json()["report_id"]

    unsold_filter = client.get("/reports?sold=false", headers=owner_headers)
    assert unsold_filter.status_code == 200
    assert unsold_filter.json()["total"] == 1
    assert unsold_filter.json()["items"][0]["report_id"] == first.json()["report_id"]

    searched = client.get(f"/reports?search={first.json()['report_id']}", headers=owner_headers)
    assert searched.status_code == 200
    assert searched.json()["total"] == 1
    assert searched.json()["items"][0]["report_id"] == first.json()["report_id"]

    advanced = client.get(
        "/reports?shape=Oval&color_grade=2&clarity_grade=3&sort=shape_asc",
        headers=owner_headers,
    )
    assert advanced.status_code == 200
    assert advanced.json()["total"] == 1
    assert advanced.json()["items"][0]["report_id"] == first.json()["report_id"]

    admin_filtered = client.get(
        f"/reports?expert_id={experts['other'].expert_id}", headers=admin_headers
    )
    assert admin_filtered.status_code == 200
    assert admin_filtered.json()["total"] == 1
    assert admin_filtered.json()["items"][0]["report_id"] == other.json()["report_id"]

    assert client.get("/reports?page_size=101", headers=owner_headers).status_code == 422
    assert client.get("/reports?price_min=-1", headers=owner_headers).status_code == 422
