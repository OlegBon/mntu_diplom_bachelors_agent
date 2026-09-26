from io import BytesIO

import pytest
from pypdf import PdfReader

from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_demo_preview_pdf_embeds_only_bundled_synthetic_assets(client, db_session, experts) -> None:
    create_demo_report(db_session, experts)
    headers = auth_headers(client, experts["admin"].username)

    response = client.get(
        f"/demo/datasets/{DATASET_ID}/reports/DEMO-00001/passport-preview/pdf",
        headers=headers,
    )

    assert response.status_code == 200
    document = PdfReader(BytesIO(response.content))
    assert len(document.pages) == 3
    text = "\n".join(page.extract_text() or "" for page in document.pages)
    assert "DEMO" in text
    assert "Synthetic asset" in text
    assert "QR" not in text
