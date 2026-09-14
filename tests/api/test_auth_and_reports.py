import pytest

from backend import models
from tests.conftest import auth_headers


def diamond_payload() -> dict[str, object]:
    return {
        "shape": "Round",
        "stone_origin": 0,
        "carat_weight": 1.0,
        "color_grade": 1,
        "clarity_grade": 1,
        "measurements_length": 6.0,
        "measurements_width": 6.0,
        "measurements_depth": 4.0,
        "table_percent": 58.0,
        "depth_percent": 61.0,
        "crown_angle": 34.5,
        "pavilion_angle": 40.8,
        "polish_grade": 0,
        "symmetry_grade": 0,
        "fluorescence_grade": 0,
        "price": 1000.0,
    }


@pytest.mark.api
@pytest.mark.integration
def test_login_and_protected_profile(client, experts) -> None:
    assert client.get("/users/me").status_code == 401

    headers = auth_headers(client, experts["owner"].username)
    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == experts["owner"].username
    assert client.post("/token", data={"username": experts["owner"].username, "password": "wrong"}).status_code == 401


@pytest.mark.api
@pytest.mark.integration
def test_experts_returns_non_admin_users(client, experts) -> None:
    response = client.get("/experts/", headers=auth_headers(client, experts["owner"].username))

    assert response.status_code == 200
    assert {expert["username"] for expert in response.json()} == {
        experts["owner"].username,
        experts["other"].username,
    }


@pytest.mark.api
@pytest.mark.integration
def test_create_report_persists_seconds_and_dashboard_fields(client, db_session, experts) -> None:
    response = client.post(
        "/diamonds/",
        json=diamond_payload(),
        headers=auth_headers(client, experts["owner"].username),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["shape"] == "Round"
    assert body["cut_grade"] == 0
    stored = db_session.get(models.DiamondReport, body["report_id"])
    assert stored is not None
    assert 300 <= stored.evaluation_time_sec <= 2400
    assert stored.evaluation_time_sec % 60 == 0


@pytest.mark.api
@pytest.mark.integration
def test_report_update_requires_owner_or_admin(client, experts, report) -> None:
    update = {"price": 1200.0}
    owner = client.put(f"/diamonds/{report.report_id}", json=update, headers=auth_headers(client, experts["owner"].username))
    other = client.put(f"/diamonds/{report.report_id}", json=update, headers=auth_headers(client, experts["other"].username))
    admin = client.put(f"/diamonds/{report.report_id}", json=update, headers=auth_headers(client, experts["admin"].username))

    assert owner.status_code == 200
    assert other.status_code == 403
    assert admin.status_code == 200


@pytest.mark.api
@pytest.mark.integration
def test_report_update_and_delete_return_404_when_missing(client, experts) -> None:
    headers = auth_headers(client, experts["admin"].username)

    assert client.put("/diamonds/DR-MISSING", json={"price": 1200.0}, headers=headers).status_code == 404
    assert client.delete("/diamonds/DR-MISSING", headers=headers).status_code == 404


@pytest.mark.api
@pytest.mark.integration
def test_admin_can_delete_existing_report(client, db_session, experts, report) -> None:
    response = client.delete(
        f"/diamonds/{report.report_id}",
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 200
    assert db_session.get(models.DiamondReport, report.report_id) is None


@pytest.mark.api
@pytest.mark.integration
def test_report_create_validates_required_fields(client, experts) -> None:
    response = client.post("/diamonds/", json={}, headers=auth_headers(client, experts["owner"].username))

    assert response.status_code == 422
