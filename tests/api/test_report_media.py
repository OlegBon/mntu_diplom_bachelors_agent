from pathlib import Path

import pytest

from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


MINIMAL_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


def create_draft_report(client, headers: dict[str, str]) -> str:
    response = client.post("/reports", json=report_payload(), headers=headers)
    assert response.status_code == 200
    return response.json()["report_id"]


@pytest.mark.api
@pytest.mark.integration
def test_report_media_is_private_and_owner_can_upload_read_and_delete(
    client,
    experts,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(tmp_path / "private-media"))
    owner_headers = auth_headers(client, experts["owner"].username)
    report_id = create_draft_report(client, owner_headers)

    uploaded = client.post(
        f"/reports/{report_id}/media",
        data={"asset_type": "stone_photo"},
        files={"file": ("stone.png", MINIMAL_PNG, "image/png")},
        headers=owner_headers,
    )

    assert uploaded.status_code == 200
    asset = uploaded.json()
    assert asset["asset_type"] == "stone_photo"
    assert asset["mime_type"] == "image/png"
    assert asset["is_public"] is False
    assert (tmp_path / "private-media" / report_id).is_dir()

    other_headers = auth_headers(client, experts["other"].username)
    assert client.get(f"/reports/{report_id}/media", headers=other_headers).status_code == 403
    assert (
        client.get(
            f"/reports/{report_id}/media/{asset['media_id']}/content",
            headers=other_headers,
        ).status_code
        == 403
    )

    content = client.get(
        f"/reports/{report_id}/media/{asset['media_id']}/content",
        headers=owner_headers,
    )
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("image/png")
    assert content.content == MINIMAL_PNG

    deleted = client.delete(
        f"/reports/{report_id}/media/{asset['media_id']}",
        headers=owner_headers,
    )
    assert deleted.status_code == 200
    assert client.get(f"/reports/{report_id}/media", headers=owner_headers).json() == []


@pytest.mark.api
@pytest.mark.integration
def test_report_media_rejects_spoofed_type_and_allows_admin_access(
    client,
    experts,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(tmp_path / "private-media"))
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    report_id = create_draft_report(client, owner_headers)

    spoofed = client.post(
        f"/reports/{report_id}/media",
        data={"asset_type": "stone_photo"},
        files={"file": ("not-an-image.png", b"not an image", "image/png")},
        headers=owner_headers,
    )
    assert spoofed.status_code == 422

    uploaded = client.post(
        f"/reports/{report_id}/media",
        data={"asset_type": "supporting_document"},
        files={"file": ("proof.pdf", b"%PDF-1.7\nproof", "application/pdf")},
        headers=owner_headers,
    )
    assert uploaded.status_code == 200

    admin_list = client.get(f"/reports/{report_id}/media", headers=admin_headers)
    assert admin_list.status_code == 200
    assert len(admin_list.json()) == 1
