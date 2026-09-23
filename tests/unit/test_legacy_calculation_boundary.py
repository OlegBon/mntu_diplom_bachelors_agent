from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_unsafe_legacy_bulk_recalculation_script_is_retired():
    assert not (PROJECT_ROOT / "scripts" / "recalc_grades.py").exists()


def test_legacy_and_ml_boundary_decision_records_required_safeguards():
    decision = (
        PROJECT_ROOT / "docs" / "decisions" / "004-legacy-calculation-and-ml-boundary.md"
    ).read_text(encoding="utf-8")

    for safeguard in ("--dry-run", "explicit scope", "audit trail", "rollback plan"):
        assert safeguard in decision

    assert "ML не може змінювати system/expert grades" in decision
