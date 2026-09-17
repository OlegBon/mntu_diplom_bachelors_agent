from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend import models
from backend.market_providers import FetchedMarketSnapshot, MarketQuote
from tests.conftest import auth_headers


def _register_openfacet(db_session) -> None:
    db_session.add(models.MarketDataProvider(
        provider_code="openfacet",
        display_name="OpenFacet",
        provider_type="market_reference",
        documentation_url="https://openfacet.net/en/api-docs/",
        terms_url="https://openfacet.net/en/terms/",
        scope_note="Comparable natural GIA reference only.",
        is_active=True,
    ))
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
    _register_openfacet(db_session)
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

    assert client.get("/market-data/providers").status_code == 401
    assert client.get("/market-data/providers", headers=owner_headers).status_code == 403
    assert client.get("/market-data/providers", headers=admin_headers).json()[0]["provider_code"] == "openfacet"

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

    values = client.get(f"/reports/{report_id}/valuations", headers=owner_headers)
    assert values.status_code == 200
    assert values.json()[0]["source_name"] == "OpenFacet"
    assert client.get(f"/reports/{report_id}", headers=owner_headers).json()["price"] is None


@pytest.mark.api
@pytest.mark.integration
def test_market_data_snapshot_cannot_be_decided_twice(client, experts, db_session) -> None:
    _register_openfacet(db_session)
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
