"""Run due market-provider operations once for Windows Task Scheduler or cron.

This command is intentionally not started by FastAPI.  It makes external
requests only when one configured provider is due, and it records every result
in ``diamond_market.market_provider_operations``.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.database import SessionLocal  # noqa: E402
from backend.market_operations import run_due_provider_operations  # noqa: E402


def main() -> int:
    """Process only due schedules and return a conventional process code."""
    db = SessionLocal()
    try:
        operations = run_due_provider_operations(db)
    finally:
        db.close()
    if not operations:
        print("Немає due-операцій ринкових провайдерів.")
        return 0
    for operation in operations:
        print(
            f"{operation.provider_code}: {operation.status} "
            f"(attempt {operation.attempt_number})"
        )
    return 1 if any(operation.status == "failed" for operation in operations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
