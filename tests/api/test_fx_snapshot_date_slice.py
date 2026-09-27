from datetime import date, datetime
from decimal import Decimal

import pytest

from backend import models
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_fx_snapshot_endpoint_filters_nbu_rows_by_official_rate_date(client, db_session, experts) -> None:
    db_session.add(models.MarketDataProvider(
        provider_code="nbu",
        display_name="NBU",
        provider_type="fx_reference",
        documentation_url="https://bank.gov.ua/ua/markets/exchangerates",
        terms_url="https://bank.gov.ua/ua/about/terms-of-use",
        scope_note="Official USD/UAH rate.",
        is_active=True,
    ))
    db_session.add_all((
        models.FxDataSnapshot(
            provider_code="nbu", base_currency_code="USD", quote_currency_code="UAH",
            rate=Decimal("40.0000"), rate_date=date(2026, 9, 1),
            source_url="https://bank.gov.ua/example/old", retrieved_at=datetime(2026, 9, 1, 9),
        ),
        models.FxDataSnapshot(
            provider_code="nbu", base_currency_code="USD", quote_currency_code="UAH",
            rate=Decimal("41.0000"), rate_date=date(2026, 9, 2),
            source_url="https://bank.gov.ua/example/new", retrieved_at=datetime(2026, 9, 2, 9),
        ),
    ))
    db_session.commit()

    response = client.get(
        "/market-data/fx-snapshots",
        params={"date_from": "2026-09-02", "date_to": "2026-09-02"},
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 200
    assert [row["rate_date"] for row in response.json()] == ["2026-09-02"]


@pytest.mark.api
@pytest.mark.integration
def test_fx_snapshot_endpoint_rejects_an_inverted_date_slice(client, experts) -> None:
    response = client.get(
        "/market-data/fx-snapshots",
        params={"date_from": "2026-09-03", "date_to": "2026-09-02"},
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 422
