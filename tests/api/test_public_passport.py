import pytest

from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


def issue_report(client, experts) -> tuple[str, dict[str, str], dict[str, str]]:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    created = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers)
    assert created.status_code == 200
    report_id = created.json()["report_id"]
    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "review", "reason": None},
        headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "issued", "reason": "Approved"},
        headers=admin_headers,
    ).status_code == 200
    return report_id, owner_headers, admin_headers


@pytest.mark.api
@pytest.mark.integration
def test_only_admin_can_publish_an_issued_report_and_public_view_is_allow_listed(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    draft = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers)
    draft_id = draft.json()["report_id"]
    assert client.post(f"/reports/{draft_id}/passport", headers=owner_headers).status_code == 403
    assert client.post(f"/reports/{draft_id}/passport", headers=auth_headers(client, experts["admin"].username)).status_code == 422

    report_id, owner_headers, admin_headers = issue_report(client, experts)
    assert client.post(f"/reports/{report_id}/passport", headers=owner_headers).status_code == 403
    published = client.post(f"/reports/{report_id}/passport", headers=admin_headers)
    assert published.status_code == 200
    public_id = published.json()["public_id"]
    assert public_id != report_id
    assert len(public_id) >= 32

    public = client.get(f"/public/passports/{public_id}")
    assert public.status_code == 200
    body = public.json()
    assert body["report_id"] == report_id
    assert body["shape"] == "Round"
    assert {"price", "expert_comment", "expert_id", "market_status", "media"}.isdisjoint(body)

    qr_url = f"http://localhost:3000/passport.html?id={public_id}"
    qr = client.get(
        f"/reports/{report_id}/passport/qr",
        params={"public_url": qr_url},
        headers=admin_headers,
    )
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in qr.content
    assert client.get(
        f"/reports/{report_id}/passport/qr",
        params={"public_url": qr_url},
        headers=owner_headers,
    ).status_code == 403
    assert client.get(
        f"/reports/{report_id}/passport/qr",
        params={"public_url": "https://example.invalid/passport.html?id=other"},
        headers=admin_headers,
    ).status_code == 422


@pytest.mark.api
@pytest.mark.integration
def test_public_passport_reissue_revoke_and_void_are_immediately_opaque(client, experts) -> None:
    report_id, _owner_headers, admin_headers = issue_report(client, experts)
    first = client.post(f"/reports/{report_id}/passport", headers=admin_headers)
    first_id = first.json()["public_id"]
    second = client.post(f"/reports/{report_id}/passport/reissue", headers=admin_headers)
    second_id = second.json()["public_id"]
    assert first_id != second_id
    assert client.get(f"/public/passports/{first_id}").status_code == 404
    assert client.get(f"/public/passports/{second_id}").status_code == 200

    assert client.delete(f"/reports/{report_id}/passport", headers=admin_headers).status_code == 204
    assert client.get(f"/public/passports/{second_id}").status_code == 404

    third = client.post(f"/reports/{report_id}/passport", headers=admin_headers)
    third_id = third.json()["public_id"]
    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "void", "reason": "Revoked report"},
        headers=admin_headers,
    ).status_code == 200
    assert client.get(f"/public/passports/{third_id}").status_code == 404
    assert client.get("/public/passports/not-a-real-passport").status_code == 404
