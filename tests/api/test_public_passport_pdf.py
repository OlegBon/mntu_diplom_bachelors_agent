from io import BytesIO

import pytest
from pypdf import PdfReader

from tests.api.test_public_passport import issue_report


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
