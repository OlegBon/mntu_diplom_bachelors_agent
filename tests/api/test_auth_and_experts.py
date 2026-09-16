import pytest

from tests.conftest import auth_headers


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
