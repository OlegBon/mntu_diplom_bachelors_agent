"""Official NBU USD/UAH fetch and deterministic conversion helpers.

This module has no database side effects. The route/domain layer decides when a
fresh result becomes an immutable snapshot associated with a valuation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


NBU_USD_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?json&valcode=USD"


class FxProviderError(RuntimeError):
    """A controlled NBU failure that must not silently reuse a stale rate."""


@dataclass(frozen=True)
class NbuUsdUahRate:
    rate: Decimal
    rate_date: date
    retrieved_at: datetime
    source_url: str = NBU_USD_URL


def fetch_nbu_usd_uah(*, timeout_seconds: float = 10.0) -> NbuUsdUahRate:
    """Fetch the current official NBU UAH-per-USD observation."""
    try:
        request = Request(NBU_USD_URL, headers={"User-Agent": "DiamantID-market-reference/1.0"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed official HTTPS endpoint
            rows = json.loads(response.read().decode("utf-8"))
        row = next(item for item in rows if item.get("cc") == "USD")
        return NbuUsdUahRate(
            rate=Decimal(str(row["rate"])),
            rate_date=datetime.strptime(row["exchangedate"], "%d.%m.%Y").date(),
            retrieved_at=datetime.now(timezone.utc),
        )
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError, KeyError, StopIteration, InvalidOperation, ValueError) as error:
        raise FxProviderError("НБУ тимчасово не повернув коректний офіційний курс USD/UAH") from error


def convert_usd_to_uah(amount_usd: Decimal, rate_uah_per_usd: Decimal) -> Decimal:
    """Return an immutable UAH projection, rounded HALF_UP to two decimals."""
    return (amount_usd * rate_uah_per_usd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
