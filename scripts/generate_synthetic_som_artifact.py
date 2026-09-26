"""Create a reproducible SOM artifact for an already verified demo dataset.

The command is read-only by default.  ``--apply`` inserts immutable artifact
metadata and assignments only; it does not change demo reports, stones,
references, workflow records, accounts, or operational data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend import crud, models
from backend.database import SessionLocal
from backend.synthetic_som import ARTIFACT_VERSION, POLICY_SCENARIO_ID


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare immutable synthetic SOM artifact")
    parser.add_argument("--dataset", default="synthetic-demo-v4")
    parser.add_argument("--apply", action="store_true", help="write the artifact and its assignments")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        dataset = crud.require_demo_dataset_analysis_eligibility(db, dataset_id=args.dataset, scenario="synthetic_som")
        if not args.apply:
            print({
                "dataset_id": dataset.dataset_id,
                "artifact_version": ARTIFACT_VERSION,
                "policy_scenario_id": POLICY_SCENARIO_ID,
                "action": "dry-run; pass --apply to write only immutable SOM artifact rows",
            })
            return
        artifact = crud.build_demo_som_artifact(db, dataset_id=args.dataset)
        db.commit()
        count = db.query(models.DemoSomAssignment).filter_by(artifact_id=artifact.artifact_id).count()
        print({"artifact_id": artifact.artifact_id, "dataset_id": artifact.dataset_id, "assignment_count": count})
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
