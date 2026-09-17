from decimal import Decimal

from backend.fx import convert_usd_to_uah


def test_nbu_conversion_uses_decimal_half_up_rounding() -> None:
    assert convert_usd_to_uah(Decimal("10.005"), Decimal("1")) == Decimal("10.01")
