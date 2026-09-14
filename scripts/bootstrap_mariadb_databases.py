"""Create missing local Diamant ID MariaDB databases without deleting data."""

from __future__ import annotations

import sys
from pathlib import Path

import mysql.connector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.config import get_mariadb_connection_options  # noqa: E402


DATABASES = ("diamond_oltp", "diamond_market", "diamond_analytics")


def bootstrap_databases() -> None:
    """Create only missing databases; existing databases and tables are intact."""
    connection = mysql.connector.connect(**get_mariadb_connection_options())
    cursor = connection.cursor()
    try:
        for database_name in DATABASES:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
        connection.commit()
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    bootstrap_databases()
    print("Локальні MariaDB databases перевірено: відсутні створено, наявні не змінено.")
