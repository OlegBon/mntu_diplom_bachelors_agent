from decimal import Decimal

import pytest

from backend import models
from tests.conftest import auth_headers


def report_payload() -> dict[str, object]:
    return {
        "shape": "Round",
        "stone_origin": 0,
        "carat_weight": 1.0,
        "color_grade": 1,
        "clarity_grade": 1,
        "measurements_length": 6.0,
        "measurements_width": 6.0,
        "measurements_depth": 4.0,
        "table_percent": 58.0,
        "depth_percent": 61.0,
        "crown_angle": 34.5,
        "pavilion_angle": 40.8,
        "polish_grade": 0,
        "symmetry_grade": 0,
        "fluorescence_grade": 0,
        "price": 1000.0,
    }


@pytest.mark.api
@pytest.mark.integration
def test_admin_cannot_create_primary_report(client, db_session, experts) -> None:
    response = client.post(
        "/diamonds/",
        json=report_payload(),
        headers=auth_headers(client, experts["admin"].username),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only gemologists can create reports"
    assert db_session.query(models.DiamondReport).count() == 0


@pytest.mark.api
@pytest.mark.integration
def test_gemologist_can_create_primary_report(client, db_session, experts) -> None:
    response = client.post(
        "/diamonds/",
        json=report_payload(),
        headers=auth_headers(client, experts["owner"].username),
    )

    assert response.status_code == 200
    stored_report = db_session.get(models.DiamondReport, response.json()["report_id"])
    assert stored_report is not None
    assert stored_report.expert_id == experts["owner"].expert_id
    assert stored_report.price == Decimal("1000.00")
