from datetime import datetime, timedelta, timezone

from backend import models
from tests.conftest import auth_headers, create_expert


def seed_provider(db_session):
    db_session.add(models.MarketDataProvider(
        provider_code="partner-test", display_name="Partner test", provider_type="market_reference",
        documentation_url="https://example.invalid/docs", terms_url="https://example.invalid/terms",
        scope_note="Internal test provider", is_active=True,
    ))
    db_session.commit()


def test_partner_controls_gate_policy_api_and_write_audit(client, db_session, experts):
    seed_provider(db_session)
    headers = auth_headers(client, experts["admin"].username)
    assert client.get("/market-data/provider-access-policies", headers=headers).status_code == 403

    enabled = client.put("/users/me/partner-controls-access", headers=headers, json={"enabled": True})
    assert enabled.status_code == 200
    assert enabled.json()["partner_controls_enabled"] is True

    policy = client.put("/market-data/provider-access-policies/partner-test", headers=headers, json={
        "access_mode": "restricted_trial", "trial_expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "daily_request_limit": 10, "natural_only": True, "internal_only": True,
        "public_display_allowed": False, "ml_allowed": False, "terms_reference": "Internal approval",
    })
    assert policy.status_code == 200
    assert policy.json()["access_mode"] == "restricted_trial"
    events = client.get("/market-data/provider-access-events?provider_code=partner-test", headers=headers)
    assert events.status_code == 200
    assert events.json()[0]["action"] == "policy_updated"


def test_restricted_trial_requires_its_safety_bounds(client, db_session, experts):
    seed_provider(db_session)
    headers = auth_headers(client, experts["admin"].username)
    client.put("/users/me/partner-controls-access", headers=headers, json={"enabled": True})
    rejected = client.put("/market-data/provider-access-policies/partner-test", headers=headers, json={
        "access_mode": "restricted_trial", "natural_only": True, "internal_only": True,
        "public_display_allowed": False, "ml_allowed": False,
    })
    assert rejected.status_code == 422


def test_restricted_trial_assignment_is_audited(client, db_session, experts):
    seed_provider(db_session)
    second_admin = create_expert(db_session, username="second-admin", role="admin")
    headers = auth_headers(client, experts["admin"].username)
    client.put("/users/me/partner-controls-access", headers=headers, json={"enabled": True})
    client.put("/market-data/provider-access-policies/partner-test", headers=headers, json={
        "access_mode": "restricted_trial", "trial_expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "daily_request_limit": 10, "natural_only": True, "internal_only": True,
        "public_display_allowed": False, "ml_allowed": False,
    })
    assigned = client.put(
        f"/market-data/provider-access-policies/partner-test/assignments/{second_admin.expert_id}",
        headers=headers, json={"enabled": True},
    )
    assert assigned.status_code == 200
    policies = client.get("/market-data/provider-access-policies", headers=headers).json()
    assert policies[0]["assigned_admin_ids"] == [second_admin.expert_id]
    events = client.get("/market-data/provider-access-events?provider_code=partner-test", headers=headers).json()
    assert {event["action"] for event in events} >= {"policy_updated", "trial_admin_assigned"}


def test_gemologist_cannot_enable_partner_controls(client, experts):
    headers = auth_headers(client, experts["owner"].username)
    assert client.put("/users/me/partner-controls-access", headers=headers, json={"enabled": True}).status_code == 403
