"""Canonical logical database topology shared by local and future runtimes.

MariaDB treats these names as separate physical databases.  PostgreSQL will
keep the same names as schemas inside one physical database.  The application
models always use the logical names explicitly.
"""

from __future__ import annotations


LOCAL_DEFAULT_DATABASE = "diamond_oltp"
MANAGED_SCHEMAS: tuple[str, str, str] = (
    "diamond_oltp",
    "diamond_market",
    "diamond_analytics",
)
