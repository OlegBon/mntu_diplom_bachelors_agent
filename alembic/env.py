"""Alembic environment for the three local Diamant ID MariaDB databases."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend import models  # noqa: F401 - imports all ORM tables into Base.metadata
from backend.config import get_database_url
from backend.database import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
MANAGED_SCHEMAS = {"diamond_oltp", "diamond_market", "diamond_analytics"}


def include_name(name, type_, parent_names):
    """Limit autogenerate to the three databases owned by Diamant ID."""
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def run_migrations_offline() -> None:
    """Generate SQL only; no database connection or mutation is performed."""
    context.configure(
        url=str(get_database_url()),
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        version_table_schema="diamond_oltp",
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations after the non-destructive MariaDB database bootstrap."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(get_database_url())
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema="diamond_oltp",
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()
