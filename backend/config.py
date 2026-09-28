"""Безпечне завантаження локальної конфігурації Diamant ID."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

from .database_topology import LOCAL_DEFAULT_DATABASE


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_required_env(name: str) -> str:
    """Повернути обов'язкову непорожню змінну середовища без її логування."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Потрібно задати змінну середовища {name}.")
    return value


def get_bounded_int_env(name: str, *, default: int, minimum: int, maximum: int) -> int:
    """Read a bounded integer setting without exposing environment contents."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"Змінна середовища {name} має бути цілим числом.") from error
    if not minimum <= value <= maximum:
        raise RuntimeError(f"Змінна середовища {name} має бути в межах {minimum}–{maximum}.")
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
        database=os.getenv("DB_NAME", LOCAL_DEFAULT_DATABASE),
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


def get_media_storage_root() -> Path:
    """Return the local private media directory without creating it on import."""
    configured_path = os.getenv("MEDIA_STORAGE_PATH")
    if configured_path and configured_path.strip():
        return Path(configured_path.strip()).expanduser().resolve()
    return (PROJECT_ROOT / "storage" / "reports").resolve()
