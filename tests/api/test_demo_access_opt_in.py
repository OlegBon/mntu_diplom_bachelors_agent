import pytest

from tests.api.test_demo_dataset_isolation import DATASET_ID, create_demo_report
from tests.conftest import auth_headers, create_expert


@pytest.mark.api
@pytest.mark.integration
def test_demo_requires_explicit_admin_opt_in_and_allows_only_self_service(client, db_session, experts) -> None:
    create_demo_report(db_session, experts)
    disabled_admin = create_expert(db_session, username="disabled-admin", role="admin")
    disabled_headers = auth_headers(client, disabled_admin.username)

    for path in (
        f"/demo/datasets/{DATASET_ID}",
        f"/demo/datasets/{DATASET_ID}/reports",
        f"/demo/datasets/{DATASET_ID}/reports/DEMO-00001",
        f"/demo/datasets/{DATASET_ID}/reports/DEMO-00001/passport-preview/pdf",
        f"/demo/datasets/{DATASET_ID}/workflow-analytics",
    ):
        assert client.get(path, headers=disabled_headers).status_code == 404

    assert client.get("/users/me", headers=disabled_headers).json()["demo_access_enabled"] is False
    enabled = client.put("/users/me/demo-access", json={"enabled": True}, headers=disabled_headers)
    assert enabled.status_code == 200
    assert enabled.json()["demo_access_enabled"] is True
    assert client.get(f"/demo/datasets/{DATASET_ID}", headers=disabled_headers).status_code == 200

    owner_headers = auth_headers(client, experts["owner"].username)
    assert client.put("/users/me/demo-access", json={"enabled": True}, headers=owner_headers).status_code == 404
