from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from tests.api.test_public_passport import issue_report
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


VALID_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _upload_image(client, report_id: str, headers: dict[str, str], asset_type: str) -> dict[str, object]:
    response = client.post(
        f"/reports/{report_id}/media",
        data={"asset_type": asset_type},
        files={"file": (f"{asset_type}.png", VALID_PNG, "image/png")},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.api
@pytest.mark.integration
def test_admin_downloads_allow_listed_public_passport_pdf(client, experts) -> None:
    report_id, owner_headers, admin_headers = issue_report(client, experts)
    published = client.post(f"/reports/{report_id}/passport", headers=admin_headers)
    public_id = published.json()["public_id"]
    public_url = f"http://localhost:3000/passport.html?id={public_id}"

    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": public_url},
        headers=owner_headers,
    ).status_code == 403
    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": f"http://localhost:3000/passport.html?id={report_id}"},
        headers=admin_headers,
    ).status_code == 422

    response = client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": public_url},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert f'filename="passport-{report_id}.pdf"' in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")

    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages)
    assert "Публічний паспорт" in text
    assert report_id in text
    assert public_id in text
    assert public_url in text
    assert "Initial observation" not in text
    assert "not_for_sale" not in text

    assert client.delete(f"/reports/{report_id}/passport", headers=admin_headers).status_code == 204
    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": public_url},
        headers=admin_headers,
    ).status_code == 404


@pytest.mark.api
@pytest.mark.integration
def test_pdf_uses_only_the_current_passport_and_closes_after_void(client, experts) -> None:
    report_id, _owner_headers, admin_headers = issue_report(client, experts)
    first = client.post(f"/reports/{report_id}/passport", headers=admin_headers).json()["public_id"]
    second = client.post(f"/reports/{report_id}/passport/reissue", headers=admin_headers).json()["public_id"]
    first_url = f"http://localhost:3000/passport.html?id={first}"
    second_url = f"http://localhost:3000/passport.html?id={second}"

    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": first_url},
        headers=admin_headers,
    ).status_code == 422
    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": second_url},
        headers=admin_headers,
    ).status_code == 200

    assert client.post(
        f"/reports/{report_id}/transitions",
        json={"target_status": "void", "reason": "Passport no longer valid"},
        headers=admin_headers,
    ).status_code == 200
    assert client.get(
        f"/reports/{report_id}/passport/pdf",
        params={"public_url": second_url},
        headers=admin_headers,
    ).status_code == 404


@pytest.mark.api
@pytest.mark.integration
def test_pdf_contains_only_current_verified_public_media(client, experts, monkeypatch, tmp_path: Path) -> None:
    storage_root = tmp_path / "private-media"
    monkeypatch.setenv("MEDIA_STORAGE_PATH", str(storage_root))
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    report_id = client.post("/reports", json=report_payload(confirmed=True), headers=owner_headers).json()["report_id"]
    photo = _upload_image(client, report_id, owner_headers, "stone_photo")
    plotting = _upload_image(client, report_id, owner_headers, "plotting_diagram")
    _upload_image(client, report_id, owner_headers, "instrument_image")
    assert client.post(f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": None}, headers=owner_headers).status_code == 200
    assert client.post(f"/reports/{report_id}/transitions", json={"target_status": "issued", "reason": "Approved"}, headers=admin_headers).status_code == 200
    for asset in (photo, plotting):
        assert client.put(f"/reports/{report_id}/media/{asset['media_id']}/publication", json={"is_public": True}, headers=admin_headers).status_code == 200
    passport = client.post(f"/reports/{report_id}/passport", headers=admin_headers).json()
    public_url = f"http://localhost:3000/passport.html?id={passport['public_id']}"

    response = client.get(f"/reports/{report_id}/passport/pdf", params={"public_url": public_url}, headers=admin_headers)
    assert response.status_code == 200
    assert len(PdfReader(BytesIO(response.content)).pages) == 3

    for stored_image in (storage_root / report_id).glob("*.png"):
        stored_image.write_bytes(b"tampered")
    tampered = client.get(f"/reports/{report_id}/passport/pdf", params={"public_url": public_url}, headers=admin_headers)
    assert tampered.status_code == 200
    assert len(PdfReader(BytesIO(tampered.content)).pages) == 1

    assert client.put(f"/reports/{report_id}/media/{plotting['media_id']}/publication", json={"is_public": False}, headers=admin_headers).status_code == 200
    assert client.put(f"/reports/{report_id}/media/{photo['media_id']}/publication", json={"is_public": False}, headers=admin_headers).status_code == 200
    unpublished = client.get(f"/reports/{report_id}/passport/pdf", params={"public_url": public_url}, headers=admin_headers)
    assert unpublished.status_code == 200
    assert len(PdfReader(BytesIO(unpublished.content)).pages) == 1
