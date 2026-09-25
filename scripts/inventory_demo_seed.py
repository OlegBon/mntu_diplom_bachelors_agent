"""Read-only inventory for the historical synthetic seed range.

The script does not require migration 0014 and does not change data.  It is a
mandatory precondition for any separately approved classification of
DR-00001…DR-01000 as a demo dataset.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text

# `python scripts/inventory_demo_seed.py` sets sys.path to scripts/, while the
# documented invocation runs from the repository root. Make the local backend
# package available without relying on an installed distribution.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import engine


FIRST_ID = 1
LAST_ID = 1_000


def expected_report_ids() -> set[str]:
    return {f"DR-{number:05d}" for number in range(FIRST_ID, LAST_ID + 1)}


def inventory() -> dict[str, object]:
    """Collect range and referential-integrity facts without modifying MariaDB."""
    with engine.connect() as connection:
        report_ids = {
            row.report_id
            for row in connection.execute(text(
                "SELECT report_id FROM diamond_oltp.diamond_reports "
                "WHERE report_id >= 'DR-00001' AND report_id <= 'DR-01000'"
            ))
        }
        missing_stones = connection.execute(text(
            "SELECT COUNT(*) FROM diamond_oltp.diamond_reports "
            "WHERE report_id >= 'DR-00001' AND report_id <= 'DR-01000' AND stone_id IS NULL"
        )).scalar_one()
        orphan_events = connection.execute(text(
            "SELECT COUNT(*) FROM diamond_oltp.report_events e "
            "LEFT JOIN diamond_oltp.diamond_reports r ON r.report_id = e.report_id "
            "WHERE e.report_id >= 'DR-00001' AND e.report_id <= 'DR-01000' AND r.report_id IS NULL"
        )).scalar_one()
        operational_after_range = connection.execute(text(
            "SELECT COUNT(*) FROM diamond_oltp.diamond_reports WHERE report_id >= 'DR-01001'"
        )).scalar_one()

    expected = expected_report_ids()
    return {
        "read_only": True,
        "expected_range": "DR-00001…DR-01000",
        "expected_count": len(expected),
        "found_count": len(report_ids),
        "missing_ids": sorted(expected - report_ids),
        "unexpected_ids": sorted(report_ids - expected),
        "reports_without_stone": missing_stones,
        "orphan_events_in_range": orphan_events,
        "operational_reports_at_or_after_DR_01001": operational_after_range,
        "ready_for_separate_backfill_approval": (
            report_ids == expected and missing_stones == 0 and orphan_events == 0
        ),
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
