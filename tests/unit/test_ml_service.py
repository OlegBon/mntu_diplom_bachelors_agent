import pytest

from backend.ml_service import MLService


@pytest.mark.unit
def test_predict_price_is_deterministic_with_fixed_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(MLService, "get_market_base_price", staticmethod(lambda: 1000.0))
    monkeypatch.setattr("backend.ml_service.random.uniform", lambda _low, _high: 1.0)

    assert MLService.predict_price(1.0, 0, 0, 0) == 1000.0
