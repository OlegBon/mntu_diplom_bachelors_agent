"""Read-only repository check for the Diamant ID database topology contract.

It deliberately does not load ``.env``, build an engine, or connect to a
database.  Task 161 will add a disposable PostgreSQL runtime smoke-check.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database_topology import LOCAL_DEFAULT_DATABASE, MANAGED_SCHEMAS


def require(condition: bool, message: str) -> None:
    """Raise a concise contract error without reading private configuration."""
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    """Validate topology identifiers and the ownership of reserved data."""
    example_env = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    models_source = (PROJECT_ROOT / "backend" / "models.py").read_text(encoding="utf-8")
    config_source = (PROJECT_ROOT / "backend" / "config.py").read_text(encoding="utf-8")

    require(
        f"DB_NAME={LOCAL_DEFAULT_DATABASE}" in example_env,
        ".env.example must set DB_NAME to the local default database.",
    )
    require(
        "LOCAL_DEFAULT_DATABASE" in config_source,
        "backend.config must use the canonical local default database.",
    )
    for schema_name in MANAGED_SCHEMAS:
        require(schema_name in models_source, f"ORM metadata does not declare {schema_name}.")

    demo_som_start = models_source.index("class DemoSomArtifact")
    demo_som_end = models_source.index("class DemoSomAssignment")
    require(
        '"diamond_oltp"' in models_source[demo_som_start:demo_som_end],
        "DemoSomArtifact must remain owned by diamond_oltp.",
    )
    ml_results_start = models_source.index("class MlResult")
    require(
        '"diamond_analytics"' in models_source[ml_results_start:],
        "MLResult must remain owned by diamond_analytics.",
    )

    print(
        "Database topology contract OK: local default diamond_oltp; "
        "managed schemas diamond_oltp, diamond_market, diamond_analytics."
    )


if __name__ == "__main__":
    main()
