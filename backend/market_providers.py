"""Adapters for externally published market-reference data.

Providers return data only. Persisting a candidate, approving it and applying a
reference to a report are deliberately separate actions owned by the domain
layer. This keeps network failures outside database transactions and makes a
provider replaceable without changing report data.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OPENFACET_PROVIDER_CODE = "openfacet"
OPENFACET_BASE_URL = "https://data.openfacet.net"
OPENFACET_TERMS_URL = "https://openfacet.net/en/terms/"
OPENFACET_METHODOLOGY_URL = "https://openfacet.net/en/methodology/"
OPENFACET_SUPPORTED_SHAPES = (
    "round",
    "cushion",
    "radiant",
    "emerald",
    "oval",
    "pear",
    "marquise",
    "heart",
)


class MarketProviderError(RuntimeError):
    """A controlled external-provider failure safe to present through the API."""


@dataclass(frozen=True)
class MarketQuote:
    """One canonical OpenFacet USD-per-carat observation."""

    shape_code: str
    carat_anchor: Decimal
    color_code: str
    clarity_code: str
    price_per_carat: Decimal


@dataclass(frozen=True)
class FetchedMarketSnapshot:
    """Provider output before it is persisted as a candidate snapshot."""

    provider_code: str
    currency_code: str
    unit: str
    retrieved_at: datetime
    source_url: str
    methodology_url: str
    coverage_note: str
    quotes: tuple[MarketQuote, ...]


class OpenFacetProvider:
    """Read OpenFacet's published CSV lists without assuming an API key."""

    provider_code = OPENFACET_PROVIDER_CODE

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_snapshot(self) -> FetchedMarketSnapshot:
        quotes: list[MarketQuote] = []
        source_urls: list[str] = []
        for shape_code in OPENFACET_SUPPORTED_SHAPES:
            source_url = f"{OPENFACET_BASE_URL}/list_{shape_code}.csv"
            quotes.extend(self._fetch_shape_quotes(shape_code, source_url))
            source_urls.append(source_url)
        if not quotes:
            raise MarketProviderError("OpenFacet returned no usable price observations")
        return FetchedMarketSnapshot(
            provider_code=self.provider_code,
            currency_code="USD",
            unit="USD_PER_CARAT",
            retrieved_at=datetime.now(timezone.utc),
            source_url=",".join(source_urls),
            methodology_url=OPENFACET_METHODOLOGY_URL,
            coverage_note=(
                "Model-based retail reference: natural GIA-certified comparable stones; "
                "not an appraisal, offer, transaction or sale price."
            ),
            quotes=tuple(quotes),
        )

    def _fetch_shape_quotes(self, shape_code: str, source_url: str) -> list[MarketQuote]:
        try:
            request = Request(source_url, headers={"User-Agent": "DiamantID-market-reference/1.0"})
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed HTTPS provider URL
                body = response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as error:
            raise MarketProviderError("OpenFacet data is temporarily unavailable") from error

        reader = csv.DictReader(StringIO(body))
        required_columns = {"carat", "color", "clarity", "price"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise MarketProviderError("OpenFacet returned an unsupported CSV format")

        quotes: list[MarketQuote] = []
        try:
            for row in reader:
                quotes.append(
                    MarketQuote(
                        shape_code=shape_code,
                        carat_anchor=Decimal(row["carat"]),
                        color_code=row["color"].strip().upper(),
                        clarity_code=row["clarity"].strip().upper(),
                        price_per_carat=Decimal(row["price"]),
                    )
                )
        except (InvalidOperation, KeyError, AttributeError) as error:
            raise MarketProviderError("OpenFacet returned an invalid price observation") from error
        return quotes


def get_market_provider(provider_code: str) -> OpenFacetProvider:
    """Return the registered adapter; new providers extend this explicit registry."""
    if provider_code == OPENFACET_PROVIDER_CODE:
        return OpenFacetProvider()
    raise MarketProviderError("Unsupported market-data provider")
