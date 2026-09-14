"""Безпечне завантаження локальної конфігурації Diamant ID."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_required_env(name: str) -> str:
    """Повернути обов'язкову непорожню змінну середовища без її логування."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Потрібно задати змінну середовища {name}.")
    return value


def get_database_url() -> str | URL:
    """Повернути явний URL БД або зібрати його з локальних DB_* змінних."""
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.strip():
        return database_url.strip()

    return URL.create(
        "mysql+mysqlconnector",
        username=get_required_env("DB_USER"),
        password=os.getenv("DB_PASSWORD", ""),
        host=get_required_env("DB_HOST"),
        port=int(get_required_env("DB_PORT")),
        database=os.getenv("DB_NAME", "diamond_oltp"),
    )


def get_mariadb_connection_options() -> dict[str, str | int]:
    """Параметри raw MariaDB-з'єднання для локального руйнівного seed."""
    database_url = make_url(get_database_url())
    if not database_url.drivername.startswith("mysql"):
        raise RuntimeError("scripts/seed_db.py підтримує лише локальний MariaDB URL.")
    if database_url.host is None or database_url.username is None:
        raise RuntimeError("MariaDB URL повинен містити host і username.")

    return {
        "host": database_url.host,
        "port": database_url.port or 3306,
        "user": database_url.username,
        "password": database_url.password or "",
    }
