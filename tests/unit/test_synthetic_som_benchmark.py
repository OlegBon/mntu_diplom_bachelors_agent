from decimal import Decimal

import pytest

from backend import synthetic_som


@pytest.mark.unit
def test_synthetic_benchmark_quartiles_are_decimal_and_deterministic() -> None:
    values = [Decimal("1100"), Decimal("2200"), Decimal("3300"), Decimal("4400")]

    thresholds = synthetic_som.benchmark_quantile_thresholds(values)

    assert thresholds == (Decimal("1100"), Decimal("2200"), Decimal("3300"))
    assert [synthetic_som.benchmark_band(value, thresholds) for value in values] == ["q1", "q2", "q3", "q4"]


@pytest.mark.unit
def test_synthetic_benchmark_median_uses_exact_decimal_for_even_cell() -> None:
    assert synthetic_som.median_decimal([Decimal("10.1"), Decimal("10.3")]) == Decimal("10.2")
    assert synthetic_som.median_decimal([]) is None
    assert synthetic_som.benchmark_band(None, None) is None
