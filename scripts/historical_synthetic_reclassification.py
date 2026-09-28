"""Fail-closed dry-run contract for a future historical synthetic reclassification.

This script deliberately does not implement an apply path yet.  It proves the
approved IDs and their dependencies first; a later explicitly approved task may
add a transaction that changes only record_scope and demo_dataset_id.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import engine


def _validated_ids(values: object, field_name: str) -> list[str]:
    """Validate one reviewed explicit report-ID list."""
    if not isinstance(values, list) or not values:
        raise ValueError(f"{field_name} must be a non-empty JSON array")
    if any(not isinstance(value, str) or not value.startswith("DR-") for value in values):
        raise ValueError(f"{field_name} may contain only explicit DR-* report IDs")
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} contains duplicate report IDs")
    return sorted(values)


def load_allow_list(path: Path) -> list[str]:
    """Read a reviewed manifest and fail if its candidate inventory differs.

    There is intentionally no heuristic for deciding that a historical report is
    synthetic.  A reviewer supplies both the complete reviewed candidate
    inventory and the approved allow-list.  Their equality makes an accidental
    omission or an extra candidate a hard failure before any future write path.
    """
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("review manifest must be a JSON object")
    inventory = _validated_ids(manifest.get("reviewed_candidate_ids"), "reviewed_candidate_ids")
    allow_list = _validated_ids(manifest.get("approved_report_ids"), "approved_report_ids")
    if inventory != allow_list:
        raise ValueError("reviewed candidate inventory differs from approved allow-list")
    return allow_list


def allow_list_sha256(report_ids: list[str]) -> str:
    return hashlib.sha256("\n".join(report_ids).encode("utf-8")).hexdigest()


def dry_run(report_ids: list[str]) -> dict[str, object]:
    """Read candidates and dependency counts without issuing DML or a commit."""
    placeholders = ", ".join(f":id_{index}" for index in range(len(report_ids)))
    params = {f"id_{index}": report_id for index, report_id in enumerate(report_ids)}
    with engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT report_id, record_scope, demo_dataset_id, stone_id FROM diamond_oltp.diamond_reports "
            f"WHERE report_id IN ({placeholders}) ORDER BY report_id"
        ), params).mappings().all()
        found = [row["report_id"] for row in rows]
        dependency_counts = connection.execute(text(
            "SELECT "
            f"(SELECT COUNT(*) FROM diamond_oltp.report_events WHERE report_id IN ({placeholders})) AS events, "
            f"(SELECT COUNT(*) FROM diamond_oltp.stone_valuations WHERE report_id IN ({placeholders})) AS valuations, "
            f"(SELECT COUNT(*) FROM diamond_oltp.media_assets WHERE report_id IN ({placeholders})) AS media, "
            f"(SELECT COUNT(*) FROM diamond_oltp.public_passports WHERE report_id IN ({placeholders})) AS passports"
        ), params).mappings().one()

    missing = sorted(set(report_ids) - set(found))
    non_operational = sorted(row["report_id"] for row in rows if row["record_scope"] != "operational")
    without_stone = sorted(row["report_id"] for row in rows if row["stone_id"] is None)
    return {
        "read_only": True,
        "apply_implemented": False,
        "allow_list_count": len(report_ids),
        "allow_list_sha256": allow_list_sha256(report_ids),
        "found_ids": found,
        "missing_ids": missing,
        "non_operational_ids": non_operational,
        "reports_without_stone": without_stone,
        "dependencies": dict(dependency_counts),
        "ready_for_future_apply_design": not missing and not non_operational and not without_stone,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-list", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(dry_run(load_allow_list(args.allow_list)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
