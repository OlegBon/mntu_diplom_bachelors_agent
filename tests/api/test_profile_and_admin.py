import pytest

from tests.conftest import auth_headers, create_expert


@pytest.mark.api
@pytest.mark.integration
def test_user_can_update_only_own_profile_and_password(client, experts) -> None:
    headers = auth_headers(client, experts["owner"].username)

    profile_response = client.put(
        "/users/me/profile",
        headers=headers,
        json={"first_name": "Updated", "last_name": "Expert", "middle_name": "M"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["first_name"] == "Updated"
    assert profile_response.json()["username"] == experts["owner"].username
    assert profile_response.json()["role"] == "gemologist"

    assert client.put(
        "/users/me/password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "new-password"},
    ).status_code == 400
    assert client.put(
        "/users/me/password",
        headers=headers,
        json={"current_password": "test-password", "new_password": "new-password"},
    ).status_code == 204
    assert client.post("/token", data={"username": experts["owner"].username, "password": "new-password"}).status_code == 200


@pytest.mark.api
@pytest.mark.integration
def test_admin_creates_and_deactivates_expert_without_deleting_history(client, experts) -> None:
    admin_headers = auth_headers(client, experts["admin"].username)
    create_response = client.post(
        "/users/",
        headers=admin_headers,
        json={"username": "new-expert", "password": "new-password", "role": "gemologist"},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["is_active"] is True

    old_expert_headers = auth_headers(client, experts["owner"].username)
    response = client.post(f"/users/{experts['owner'].expert_id}/deactivate", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.get("/users/me", headers=old_expert_headers).status_code == 401
    assert client.post("/token", data={"username": experts["owner"].username, "password": "test-password"}).status_code == 401

    expert_names = {expert["username"] for expert in client.get("/experts/", headers=admin_headers).json()}
    assert experts["owner"].username not in expert_names
    assert "new-expert" in expert_names


@pytest.mark.api
@pytest.mark.integration
def test_admin_cannot_deactivate_self_or_last_active_admin(client, experts, db_session) -> None:
    admin_headers = auth_headers(client, experts["admin"].username)
    self_response = client.post(f"/users/{experts['admin'].expert_id}/deactivate", headers=admin_headers)
    assert self_response.status_code == 409

    second_admin = create_expert(db_session, username="second-admin", role="admin")
    demote_response = client.put(
        f"/users/{experts['admin'].expert_id}",
        headers=admin_headers,
        json={"role": "gemologist"},
    )
    assert demote_response.status_code == 200
    assert demote_response.json()["role"] == "gemologist"

    second_headers = auth_headers(client, second_admin.username)
    last_admin_response = client.post(
        f"/users/{second_admin.expert_id}/deactivate", headers=second_headers,
    )
    assert last_admin_response.status_code == 409


@pytest.mark.api
@pytest.mark.integration
def test_non_admin_cannot_manage_users(client, experts) -> None:
    headers = auth_headers(client, experts["owner"].username)
    assert client.get("/users/", headers=headers).status_code == 403
    assert client.post("/users/", headers=headers, json={
        "username": "blocked-user", "password": "new-password", "role": "gemologist",
    }).status_code == 403
