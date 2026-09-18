from decimal import Decimal

import pytest

from backend.market_providers import MarketProviderError, OpenFacetProvider


@pytest.mark.unit
def test_openfacet_provider_parses_decimal_csv_without_float(monkeypatch) -> None:
    provider = OpenFacetProvider(timeout_seconds=1)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"carat,color,clarity,price\n1.0,D,FL,5000.25\n"

    monkeypatch.setattr("backend.market_providers.urlopen", lambda *_args, **_kwargs: FakeResponse())
    snapshot = provider.fetch_snapshot()

    assert len(snapshot.quotes) == 8
    assert snapshot.currency_code == "USD"
    assert snapshot.unit == "USD_PER_CARAT"
    assert snapshot.quotes[0].price_per_carat == Decimal("5000.25")
    assert isinstance(snapshot.quotes[0].price_per_carat, Decimal)


@pytest.mark.unit
def test_openfacet_provider_rejects_an_invalid_csv(monkeypatch) -> None:
    provider = OpenFacetProvider(timeout_seconds=1)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"unexpected,column\n1,2\n"

    monkeypatch.setattr("backend.market_providers.urlopen", lambda *_args, **_kwargs: FakeResponse())

    with pytest.raises(MarketProviderError, match="unsupported CSV format"):
        provider.fetch_snapshot()
