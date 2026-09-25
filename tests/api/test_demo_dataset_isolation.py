from datetime import datetime
from decimal import Decimal

import pytest

from backend import crud, models
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


DATASET_ID = "synthetic-demo-v1"


def create_demo_report(db_session, experts) -> models.DiamondReport:
    dataset = models.DemoDataset(
        dataset_id=DATASET_ID,
        label="Synthetic demonstration dataset",
        version="v1",
        generator_version="test-generator-v1",
        content_sha256="a" * 64,
        provenance="synthetic-demo-v1",
        scope_note="Internal technical demonstration only.",
        analysis_eligibility='["demo_operations", "synthetic_som"]',
        record_count=1,
    )
    stone = models.Stone(
        shape="Round",
        carat_weight=Decimal("1.20"),
        color_grade=1,
        clarity_grade=1,
        measurements_length=Decimal("6.80"),
        measurements_width=Decimal("6.80"),
        measurements_depth=Decimal("4.20"),
        table_percent=Decimal("57.00"),
        depth_percent=Decimal("61.80"),
        crown_angle=Decimal("34.50"),
        pavilion_angle=Decimal("40.80"),
        polish_grade=0,
        symmetry_grade=0,
        fluorescence_grade=0,
        origin="natural",
        treatment_status="not_assessed",
        identification_status="preliminary",
        market_status="not_for_sale",
    )
    db_session.add_all((dataset, stone))
    db_session.flush()
    report = models.DiamondReport(
        report_id="DEMO-00001",
        record_scope="demo",
        demo_dataset_id=dataset.dataset_id,
        report_date=datetime(2026, 1, 1, 12, 0),
        examination_date=datetime(2026, 1, 1).date(),
        stone_id=stone.stone_id,
        status="issued",
        issued_at=datetime(2026, 1, 2, 12, 0),
        shape="Round",
        carat_weight=Decimal("1.20"),
        color_grade=1,
        clarity_grade=1,
        polish_grade=0,
        symmetry_grade=0,
        fluorescence_grade=0,
        expert_id=experts["owner"].expert_id,
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.mark.api
@pytest.mark.integration
def test_demo_scope_is_hidden_from_operational_list_and_experts(client, db_session, experts) -> None:
    create_demo_report(db_session, experts)
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)

    operational = client.get("/reports", headers=admin_headers)
    assert operational.status_code == 200
    assert operational.json()["total"] == 0
    assert client.get("/reports/DEMO-00001", headers=owner_headers).status_code == 404
    assert client.get("/reports/DEMO-00001", headers=admin_headers).status_code == 404
    assert client.get(f"/demo/datasets/{DATASET_ID}", headers=owner_headers).status_code == 404

    dataset = client.get(f"/demo/datasets/{DATASET_ID}", headers=admin_headers)
    assert dataset.status_code == 200
    assert dataset.json()["analysis_eligibility"] == ["demo_operations", "synthetic_som"]
    page = client.get(f"/demo/datasets/{DATASET_ID}/reports", headers=admin_headers)
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["report_id"] == "DEMO-00001"


@pytest.mark.api
@pytest.mark.integration
def test_regular_report_writes_and_public_projection_reject_demo(client, db_session, experts) -> None:
    report = create_demo_report(db_session, experts)
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    db_session.add(models.PublicPassport(
        report_id=report.report_id,
        public_id="demo-public-token",
        created_by_id=experts["admin"].expert_id,
        is_active=True,
    ))
    db_session.commit()

    assert client.put(f"/reports/{report.report_id}", json=report_payload(), headers=owner_headers).status_code == 404
    assert client.post(
        f"/reports/{report.report_id}/transitions",
        json={"target_status": "void"},
        headers=admin_headers,
    ).status_code == 409
    assert client.post(
        f"/reports/{report.report_id}/work-session",
        json={"action": "start", "tab_id": "a" * 16},
        headers=owner_headers,
    ).status_code == 404
    assert client.get("/public/passports/demo-public-token").status_code == 404
    assert client.get(f"/reports/{report.report_id}/passport", headers=admin_headers).status_code == 404


@pytest.mark.unit
def test_next_operational_report_id_ignores_demo_identifiers(db_session, experts) -> None:
    create_demo_report(db_session, experts)
    assert crud._next_report_id(db_session) == "DR-00001"


@pytest.mark.unit
def test_synthetic_analysis_requires_manifest_allow_list(db_session, experts) -> None:
    create_demo_report(db_session, experts)

    assert crud.require_demo_dataset_analysis_eligibility(
        db_session, dataset_id=DATASET_ID, scenario="synthetic_som",
    ).dataset_id == DATASET_ID
    with pytest.raises(crud.ReportDomainError):
        crud.require_demo_dataset_analysis_eligibility(
            db_session, dataset_id=DATASET_ID, scenario="verified_ml",
        )


@pytest.mark.api
@pytest.mark.integration
def test_admin_can_download_private_demo_preview_without_public_passport(client, db_session, experts) -> None:
    create_demo_report(db_session, experts)
    admin_headers = auth_headers(client, experts["admin"].username)
    owner_headers = auth_headers(client, experts["owner"].username)

    response = client.get(
        f"/demo/datasets/{DATASET_ID}/reports/DEMO-00001/passport-preview/pdf",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert 'filename="demo-preview-DEMO-00001.pdf"' in response.headers["content-disposition"]
    assert client.get(
        f"/demo/datasets/{DATASET_ID}/reports/DEMO-00001/passport-preview/pdf",
        headers=owner_headers,
    ).status_code == 404
    assert db_session.query(models.PublicPassport).filter_by(report_id="DEMO-00001").count() == 0
