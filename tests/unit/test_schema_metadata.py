from backend import models


def test_orm_metadata_matches_canonical_named_indexes_for_audited_tables():
    passports = models.PublicPassport.__table__
    passport_constraints = {
        constraint.name
        for constraint in passports.constraints
        if constraint.name
    }
    assert "uq_public_passports_public_id" in passport_constraints
    assert {index.name for index in passports.indexes} == {
        "ix_diamond_oltp_public_passports_report_id",
    }

    work_session_events = models.ReportWorkSessionEvent.__table__
    assert {index.name for index in work_session_events.indexes} == {
        "ix_diamond_oltp_report_work_session_events_work_session_id",
    }

    operations = models.MarketProviderOperation.__table__
    assert {index.name for index in operations.indexes} == {
        "ix_market_operation_provider_started",
    }
