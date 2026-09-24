"""Disposable FastAPI runtime for the real browser E2E scenario.

It accepts only an explicit SQLite URL and clears only ``tmp/e2e-runtime``.
It never reads or writes the local MariaDB workflow database.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = (ROOT / "tmp" / "e2e-runtime").resolve()


def prepare_environment() -> None:
    if os.environ.get("DIAMANT_E2E_MODE") != "1":
        raise RuntimeError("E2E app requires DIAMANT_E2E_MODE=1")
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url.startswith("sqlite:"):
        raise RuntimeError("E2E app requires an explicit SQLite DATABASE_URL")
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    database_path = RUNTIME_ROOT / "diamant-id-e2e.sqlite3"
    database_path.unlink(missing_ok=True)
    storage_root = RUNTIME_ROOT / "storage"
    shutil.rmtree(storage_root, ignore_errors=True)
    os.environ["MEDIA_STORAGE_PATH"] = str(storage_root)
    os.environ.setdefault("SECRET_KEY", "e2e-only-secret-not-for-production")


prepare_environment()

from backend import models  # noqa: E402
from backend.database import Base, SessionLocal, engine  # noqa: E402
from backend.main import app  # noqa: E402
from backend.security import get_password_hash  # noqa: E402


def seed_e2e_data() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        admin = models.Expert(
            username="e2e-admin", first_name="E2E", last_name="Admin",
            password_hash=get_password_hash("E2eAdmin123"), role="admin",
        )
        gemologist = models.Expert(
            username="e2e-gemologist", first_name="E2E", last_name="Gemologist",
            password_hash=get_password_hash("E2eGemologist123"), role="gemologist",
        )
        db.add_all([admin, gemologist])
        for category, label in [
            ("color", "D"), ("clarity", "FL"), ("cut", "Excellent"),
            ("polish", "Excellent"), ("symmetry", "Excellent"), ("fluorescence", "None"),
            ("proportions", "Excellent"),
        ]:
            db.add(models.GradeMapping(category=category, grade_value=0, grade_label=label))
        for category, code, label in [
            ("shape", "Round", "Round"), ("origin", "natural", "Natural"),
            ("girdle_thickness", "medium", "Medium"), ("culet_size", "none", "None"),
            ("treatment_status", "not_assessed", "Not assessed"),
            ("identification_status", "preliminary", "Preliminary"),
        ]:
            db.add(models.ReferenceValue(category=category, code=code, label=label, sort_order=1, is_active=True))
        db.commit()


seed_e2e_data()
