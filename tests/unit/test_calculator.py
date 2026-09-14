import pytest

from backend.calculator import DiamondCalculator


@pytest.mark.unit
@pytest.mark.parametrize(
    ("table", "depth", "crown", "pavilion", "expected"),
    [
        (56.0, 59.0, 33.5, 40.6, 0),
        (61.0, 63.0, 36.5, 41.0, 0),
        (53.0, 63.0, 33.5, 40.6, 1),
        (50.0, 63.0, 33.5, 40.6, 3),
    ],
)
def test_evaluate_proportions_uses_idc_boundaries(
    table: float,
    depth: float,
    crown: float,
    pavilion: float,
    expected: int,
) -> None:
    assert DiamondCalculator.evaluate_proportions(table, depth, crown, pavilion) == expected


@pytest.mark.unit
def test_calculate_final_cut_returns_worst_component() -> None:
    assert DiamondCalculator.calculate_final_cut(0, 2, 1) == 2
