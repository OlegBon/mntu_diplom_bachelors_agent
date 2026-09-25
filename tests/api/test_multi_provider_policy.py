import pytest

from tests.api.test_market_data import _register_providers
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_policy_requires_primary_to_be_enabled_and_exposes_normalized_set(client, db_session, experts) -> None:
    _register_providers(db_session)
    admin_headers = auth_headers(client, experts["admin"].username)

    rejected = client.put("/market-data/policy", headers=admin_headers, json={
        "enabled_market_provider_codes": [],
        "dashboard_primary_provider_code": "openfacet",
        "use_fx_conversion": False,
        "fx_provider_code": None,
    })
    assert rejected.status_code == 422

    updated = client.put("/market-data/policy", headers=admin_headers, json={
        "enabled_market_provider_codes": ["openfacet"],
        "dashboard_primary_provider_code": "openfacet",
        "use_fx_conversion": False,
        "fx_provider_code": None,
    })
    assert updated.status_code == 200
    assert updated.json()["enabled_market_provider_codes"] == ["openfacet"]
    assert updated.json()["dashboard_primary_provider_code"] == "openfacet"
    assert updated.json()["market_provider_code"] == "openfacet"

    no_primary = client.put("/market-data/policy", headers=admin_headers, json={
        "enabled_market_provider_codes": ["openfacet"],
        "dashboard_primary_provider_code": None,
        "use_fx_conversion": False,
        "fx_provider_code": None,
    })
    assert no_primary.status_code == 200
    assert no_primary.json()["dashboard_primary_provider_code"] is None
