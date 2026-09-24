from pathlib import Path

import pytest

from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


MINIMAL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def _upload_draft_image(client, report_id: str, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        f"/reports/{report_id}/media",
        data={"asset_type": "stone_photo"},
        files={"file": ("stone.png", MINIMAL_PNG, "image/png")},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.api
@pytest.mark.integration
def test_admin_can_publish_allow_listed_image_only_through_active_passport(
    client,
    experts,
    monkeypatch,
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "private-media"
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(storage_root))
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    created = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers)
    report_id = created.json()["report_id"]
    image = _upload_draft_image(client, report_id, owner_headers)

    assert client.put(
        f"/reports/{report_id}/media/{image['media_id']}/publication",
        json={"is_public": True}, headers=owner_headers,
    ).status_code == 403

    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "issued", "reason": "Approved"}, headers=admin_headers,
    ).status_code == 200
    assert client.put(
        f"/reports/{report_id}/media/{image['media_id']}/publication",
        json={"is_public": True}, headers=admin_headers,
    ).status_code == 200

    passport = client.post(f"/reports/{report_id}/passport", headers=admin_headers).json()
    public_id = passport["public_id"]
    listing = client.get(f"/public/passports/{public_id}/media")
    assert listing.status_code == 200
    assert listing.json() == [{"media_id": image["media_id"], "asset_type": "stone_photo", "mime_type": "image/png"}]

    content = client.get(f"/public/passports/{public_id}/media/{image['media_id']}/content")
    assert content.status_code == 200
    assert content.content == MINIMAL_PNG
    assert content.headers["cache-control"] == "no-store"
    assert content.headers["x-content-type-options"] == "nosniff"

    assert client.delete(f"/reports/{report_id}/passport", headers=admin_headers).status_code == 204
    assert client.get(f"/public/passports/{public_id}/media").status_code == 404
    assert client.get(f"/public/passports/{public_id}/media/{image['media_id']}/content").status_code == 404


@pytest.mark.api
@pytest.mark.integration
def test_public_media_rejects_private_or_tampered_assets(
    client,
    experts,
    monkeypatch,
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "private-media"
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(storage_root))
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    # Uploads are intentionally draft-only, so the future public report starts as a draft.
    draft = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers).json()
    image = _upload_draft_image(client, draft["report_id"], owner_headers)
    assert client.post(
        f"/reports/{draft['report_id']}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers,
    ).status_code == 200
    assert client.post(
        f"/reports/{draft['report_id']}/transitions", json={"target_status": "issued", "reason": "Approved"}, headers=admin_headers,
    ).status_code == 200
    passport = client.post(f"/reports/{draft['report_id']}/passport", headers=admin_headers).json()
    public_id = passport["public_id"]
    assert client.get(f"/public/passports/{public_id}/media/{image['media_id']}/content").status_code == 404

    assert client.put(
        f"/reports/{draft['report_id']}/media/{image['media_id']}/publication",
        json={"is_public": True}, headers=admin_headers,
    ).status_code == 200
    stored_file = next((storage_root / draft["report_id"]).iterdir())
    stored_file.write_bytes(b"tampered")
    assert client.get(f"/public/passports/{public_id}/media/{image['media_id']}/content").status_code == 404
