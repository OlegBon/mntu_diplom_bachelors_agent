from datetime import datetime, timezone

import pytest

from backend import models
from backend.narrative_quality import non_whitespace_char_count, word_count
from tests.api.test_report_domain import report_payload
from tests.conftest import auth_headers


@pytest.mark.api
@pytest.mark.integration
def test_narrative_quality_is_private_non_blocking_and_unicode_aware(client, experts) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    payload = report_payload(confirmed=True)
    payload["stone"]["identification_status"] = "confirmed"
    payload["stone"]["identification_method"] = "тест"
    payload["stone"]["identification_conclusion"] = ""
    payload["expert_comment"] = "камінь камінь камінь"
    report_id = client.post("/reports", json=payload, headers=owner_headers).json()["report_id"]

    assert client.get(f"/reports/{report_id}/narrative-quality").status_code == 401
    response = client.get(f"/reports/{report_id}/narrative-quality", headers=owner_headers)
    assert response.status_code == 200
    codes = {(item["field_key"], item["code"]) for item in response.json()["warnings"]}
    assert ("identification_method", "placeholder") in codes
    assert ("identification_conclusion", "status_context") in codes
    assert ("expert_comment", "repetition") in codes
    assert client.get("/statistics/narrative-quality", headers=owner_headers).status_code == 403

    assert word_count("Український текст і English words") == 5
    assert non_whitespace_char_count(" а б\nв ") == 3

    analytics = client.get("/statistics/narrative-quality", headers=admin_headers)
    assert analytics.status_code == 200
    fields = {field["field_key"]: field for field in analytics.json()["fields"]}
    assert fields["identification_method"]["non_empty_count"] == 1
    assert fields["identification_method"]["shortest"][0]["report_id"] == report_id
    assert "text" not in fields["identification_method"]["shortest"][0]
    assert fields["identification_conclusion"]["non_empty_count"] == 0


@pytest.mark.api
@pytest.mark.integration
def test_narrative_statistics_keep_current_report_text_and_event_reason_semantics(client, experts, db_session) -> None:
    owner_headers = auth_headers(client, experts["owner"].username)
    admin_headers = auth_headers(client, experts["admin"].username)
    payload = report_payload()
    payload["stone"]["identification_method"] = "Лупа та мікроскоп"
    payload["stone"]["identification_conclusion"] = "Ознаки відповідають природному походженню."
    payload["expert_comment"] = "Повний опис для перевірки."
    report_id = client.post("/reports", json=payload, headers=owner_headers).json()["report_id"]
    assert client.post(
        f"/reports/{report_id}/transitions", json={"target_status": "review", "reason": "Потрібна перевірка адміністратором."}, headers=owner_headers,
    ).status_code == 200
    db_session.query(models.DiamondReport).filter_by(report_id=report_id).update({"created_at": datetime(2025, 1, 10, tzinfo=timezone.utc)})
    db_session.query(models.ReportEvent).filter_by(report_id=report_id).update({"created_at": datetime(2025, 1, 11, tzinfo=timezone.utc)})
    db_session.commit()

    response = client.get(
        "/statistics/narrative-quality?date_from=2025-01-10&date_to=2025-01-10", headers=admin_headers,
    )
    assert response.status_code == 200
    fields = {field["field_key"]: field for field in response.json()["fields"]}
    assert fields["expert_comment"]["non_empty_count"] == 1
    assert fields["status_transition_reason"]["non_empty_count"] == 0
    assert "Поточне значення" in fields["expert_comment"]["source_semantics"]

    response = client.get(
        "/statistics/narrative-quality?date_from=2025-01-11&date_to=2025-01-11", headers=admin_headers,
    )
    fields = {field["field_key"]: field for field in response.json()["fields"]}
    assert fields["expert_comment"]["non_empty_count"] == 0
    assert fields["status_transition_reason"]["non_empty_count"] == 1
    assert fields["status_transition_reason"]["longest"][0]["report_id"] == report_id
