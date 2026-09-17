from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend import models
from backend.market_providers import FetchedMarketSnapshot, MarketQuote
from backend.fx import FxProviderError, NbuUsdUahRate
from tests.conftest import auth_headers


def _register_providers(db_session) -> None:
    db_session.add_all([models.MarketDataProvider(
        provider_code="openfacet",
        display_name="OpenFacet",
        provider_type="market_reference",
        documentation_url="https://openfacet.net/en/api-docs/",
        terms_url="https://openfacet.net/en/terms/",
        scope_note="Comparable natural GIA reference only.",
        is_active=True,
    ), models.MarketDataProvider(
        provider_code="nbu",
        display_name="NBU",
        provider_type="fx_reference",
        documentation_url="https://bank.gov.ua/ua/markets/exchangerates",
        terms_url="https://bank.gov.ua/ua/about/terms-of-use",
        scope_note="Official USD/UAH rate.",
        is_active=True,
    ), models.MarketReferencePolicy(
        policy_id=1,
        market_provider_code="openfacet",
        use_fx_conversion=True,
        fx_provider_code="nbu",
    )])
    db_session.commit()


def _fetched_snapshot() -> FetchedMarketSnapshot:
    return FetchedMarketSnapshot(
        provider_code="openfacet",
        currency_code="USD",
        unit="USD_PER_CARAT",
        retrieved_at=datetime(2026, 9, 17, tzinfo=timezone.utc),
        source_url="https://data.openfacet.net/list_round.csv",
        methodology_url="https://openfacet.net/en/methodology/",
        coverage_note="Comparable natural GIA reference only.",
        quotes=(MarketQuote("round", Decimal("1.000"), "D", "FL", Decimal("5000.00")),),
    )


def _report_payload() -> dict:
    return {
        "examination_date": "2026-09-17",
        "stone": {
            "shape": "Round", "carat_weight": 1, "color_grade": 0, "clarity_grade": 0,
            "measurements_length": 6.5, "measurements_width": 6.5, "measurements_depth": 4,
            "table_percent": 57, "depth_percent": 62, "crown_angle": 34.5, "pavilion_angle": 40.8,
            "polish_grade": 0, "symmetry_grade": 0, "fluorescence_grade": 0,
            "origin": "natural",
        },
    }


@pytest.mark.api
@pytest.mark.integration
def test_market_data_candidate_approval_and_explicit_report_attachment(client, experts, db_session, monkeypatch) -> None:
    _register_providers(db_session)
    db_session.add_all([
        models.GradeMapping(category="color", grade_value=0, grade_label="D"),
        models.GradeMapping(category="clarity", grade_value=0, grade_label="FL"),
    ])
    db_session.commit()

    class FakeProvider:
        def fetch_snapshot(self):
            return _fetched_snapshot()

    monkeypatch.setattr("backend.main.get_market_provider", lambda _code: FakeProvider())
    monkeypatch.setattr(
        "backend.main.fetch_nbu_usd_uah",
        lambda: NbuUsdUahRate(
            rate=Decimal("40.50000000"), rate_date=datetime(2026, 9, 16).date(),
            retrieved_at=datetime(2026, 9, 17, tzinfo=timezone.utc),
        ),
    )
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)

    assert client.get("/market-data/providers").status_code == 401
    assert client.get("/market-data/providers", headers=owner_headers).status_code == 403
    policy = client.get("/market-data/policy", headers=admin_headers)
    assert policy.status_code == 200
    assert policy.json()["market_provider_code"] == "openfacet"
    assert {item["provider_code"] for item in client.get("/market-data/providers", headers=admin_headers).json()} == {"nbu", "openfacet"}

    candidate = client.post("/market-data/providers/openfacet/fetch", headers=admin_headers)
    assert candidate.status_code == 200
    snapshot_id = candidate.json()["snapshot_id"]
    assert candidate.json()["status"] == "candidate"
    assert candidate.json()["quote_count"] == 1

    report = client.post("/reports", json=_report_payload(), headers=owner_headers)
    assert report.status_code == 200
    report_id = report.json()["report_id"]

    before_approval = client.post(
        f"/reports/{report_id}/valuations/market-reference",
        headers=admin_headers,
        json={"snapshot_id": snapshot_id, "applicability_confirmed": True, "applicability_note": "Admin verified comparable natural GIA scope."},
    )
    assert before_approval.status_code == 422

    approval = client.post(f"/market-data/snapshots/{snapshot_id}/approve", headers=admin_headers, json={})
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"

    attached = client.post(
        f"/reports/{report_id}/valuations/market-reference",
        headers=admin_headers,
        json={"snapshot_id": snapshot_id, "applicability_confirmed": True, "applicability_note": "Admin verified comparable natural GIA scope."},
    )
    assert attached.status_code == 200
    assert attached.json()["amount"] == "5000.00"
    assert attached.json()["market_snapshot_id"] == snapshot_id
    assert attached.json()["converted_amount"] == "202500.00"
    assert attached.json()["converted_currency_code"] == "UAH"
    assert attached.json()["fx_rate"] == "40.50000000"

    values = client.get(f"/reports/{report_id}/valuations", headers=owner_headers)
    assert values.status_code == 200
    assert values.json()[0]["source_name"] == "OpenFacet"
    assert client.get(f"/reports/{report_id}", headers=owner_headers).json()["price"] is None
    dashboard = client.get("/reports", headers=owner_headers)
    assert dashboard.status_code == 200
    listed_reference = dashboard.json()["items"][0]["market_reference"]
    assert listed_reference["amount"] == "5000.00"
    assert listed_reference["valuation_kind"] == "market_reference"
    assert listed_reference["converted_amount"] == "202500.00"
    assert listed_reference["fx_rate_date"] == "2026-09-16"


@pytest.mark.api
@pytest.mark.integration
def test_report_gets_idempotent_system_reference_from_latest_approved_snapshot(client, experts, db_session, monkeypatch) -> None:
    _register_providers(db_session)
    db_session.add_all([
        models.GradeMapping(category="color", grade_value=0, grade_label="D"),
        models.GradeMapping(category="clarity", grade_value=0, grade_label="FL"),
    ])
    db_session.commit()

    class FakeProvider:
        def fetch_snapshot(self):
            return _fetched_snapshot()

    monkeypatch.setattr("backend.main.get_market_provider", lambda _code: FakeProvider())
    monkeypatch.setattr(
        "backend.main.fetch_nbu_usd_uah",
        lambda: NbuUsdUahRate(
            rate=Decimal("40.50000000"), rate_date=datetime(2026, 9, 16).date(),
            retrieved_at=datetime(2026, 9, 17, tzinfo=timezone.utc),
        ),
    )
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)
    snapshot_id = client.post("/market-data/providers/openfacet/fetch", headers=admin_headers).json()["snapshot_id"]
    assert client.post(f"/market-data/snapshots/{snapshot_id}/approve", headers=admin_headers, json={}).status_code == 200

    report = client.post("/reports", json=_report_payload(), headers=owner_headers)
    assert report.status_code == 200
    report_id = report.json()["report_id"]
    values = client.get(f"/reports/{report_id}/valuations", headers=owner_headers).json()
    assert len(values) == 1
    assert values[0]["valuation_kind"] == "system_market_reference"
    assert values[0]["amount"] == "5000.00"
    assert values[0]["converted_amount"] == "202500.00"
    assert values[0]["applicability_note"] is None

    updated = client.put(f"/reports/{report_id}", json=_report_payload(), headers=owner_headers)
    assert updated.status_code == 200
    assert len(client.get(f"/reports/{report_id}/valuations", headers=owner_headers).json()) == 1

    listed_reference = client.get("/reports", headers=owner_headers).json()["items"][0]["market_reference"]
    assert listed_reference["valuation_kind"] == "system_market_reference"
    assert listed_reference["fx_rate"] == "40.50000000"


@pytest.mark.api
@pytest.mark.integration
def test_report_save_is_not_blocked_when_system_fx_is_unavailable(client, experts, db_session, monkeypatch) -> None:
    _register_providers(db_session)
    db_session.add_all([
        models.GradeMapping(category="color", grade_value=0, grade_label="D"),
        models.GradeMapping(category="clarity", grade_value=0, grade_label="FL"),
        models.MarketDataSnapshot(
            provider_code="openfacet", snapshot_kind="market_reference", status="approved",
            currency_code="USD", unit="USD_PER_CARAT", source_url="https://example.test/list.csv",
            methodology_url="https://example.test/methodology", coverage_note="Test coverage.",
            quote_count=1, content_sha256="b" * 64, retrieved_at=datetime(2026, 9, 17, tzinfo=timezone.utc),
            approved_at=datetime(2026, 9, 17, tzinfo=timezone.utc), created_by_id=experts["admin"].expert_id,
        ),
    ])
    db_session.commit()
    snapshot = db_session.query(models.MarketDataSnapshot).filter_by(content_sha256="b" * 64).one()
    db_session.add(models.MarketDataQuote(
        snapshot_id=snapshot.snapshot_id, shape_code="round", carat_anchor=Decimal("1.000"),
        color_code="D", clarity_code="FL", price_per_carat=Decimal("5000.00"),
    ))
    db_session.commit()
    monkeypatch.setattr("backend.main.fetch_nbu_usd_uah", lambda: (_ for _ in ()).throw(FxProviderError("NBU unavailable")))

    owner_headers = auth_headers(client, experts["owner"].username)
    report = client.post("/reports", json=_report_payload(), headers=owner_headers)
    assert report.status_code == 200
    assert client.get(f"/reports/{report.json()['report_id']}/valuations", headers=owner_headers).json() == []


@pytest.mark.api
@pytest.mark.integration
def test_admin_policy_can_disable_uah_conversion_for_future_references(client, experts, db_session, monkeypatch) -> None:
    _register_providers(db_session)
    db_session.add_all([
        models.GradeMapping(category="color", grade_value=0, grade_label="D"),
        models.GradeMapping(category="clarity", grade_value=0, grade_label="FL"),
    ])
    db_session.commit()

    class FakeProvider:
        def fetch_snapshot(self):
            return _fetched_snapshot()

    monkeypatch.setattr("backend.main.get_market_provider", lambda _code: FakeProvider())
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)
    updated_policy = client.put("/market-data/policy", headers=admin_headers, json={
        "market_provider_code": "openfacet", "use_fx_conversion": False, "fx_provider_code": None,
    })
    assert updated_policy.status_code == 200
    assert updated_policy.json()["use_fx_conversion"] is False
    snapshot_id = client.post("/market-data/providers/openfacet/fetch", headers=admin_headers).json()["snapshot_id"]
    assert client.post(f"/market-data/snapshots/{snapshot_id}/approve", headers=admin_headers, json={}).status_code == 200

    report = client.post("/reports", json=_report_payload(), headers=owner_headers)
    values = client.get(f"/reports/{report.json()['report_id']}/valuations", headers=owner_headers).json()
    assert values[0]["valuation_kind"] == "system_market_reference"
    assert values[0]["converted_amount"] is None
    assert values[0]["fx_snapshot_id"] is None


@pytest.mark.api
@pytest.mark.integration
def test_market_data_snapshot_cannot_be_decided_twice(client, experts, db_session) -> None:
    _register_providers(db_session)
    snapshot = models.MarketDataSnapshot(
        provider_code="openfacet", snapshot_kind="market_reference", status="candidate",
        currency_code="USD", unit="USD_PER_CARAT", source_url="https://example.test/list.csv",
        methodology_url="https://example.test/methodology", coverage_note="Test coverage.",
        quote_count=1, content_sha256="a" * 64, retrieved_at=datetime.now(timezone.utc),
        created_by_id=experts["admin"].expert_id,
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)

    headers = auth_headers(client, experts["admin"].username)
    assert client.post(f"/market-data/snapshots/{snapshot.snapshot_id}/reject", headers=headers, json={"reason": "Test"}).status_code == 200
    assert client.post(f"/market-data/snapshots/{snapshot.snapshot_id}/approve", headers=headers, json={}).status_code == 422
