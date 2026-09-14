"""Alembic environment for the three local Diamant ID MariaDB databases."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, create_engine, pool
from sqlalchemy.schema import BLANK_SCHEMA

from backend import models  # noqa: F401 - imports all ORM tables into Base.metadata
from backend.config import get_database_url
from backend.database import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

MANAGED_SCHEMAS = {"diamond_oltp", "diamond_market", "diamond_analytics"}


def build_comparison_metadata() -> MetaData:
    """Normalize the connected MariaDB default database for autogenerate.

    MariaDB exposes the URL database (`diamond_oltp`) as schema ``None`` in its
    inspector, while application models name it explicitly. A metadata clone
    avoids a false "add all OLTP tables" diff without changing ORM metadata or
    generated migration SQL.
    """
    metadata = MetaData()

    def referred_schema_fn(table, to_schema, constraint, referred_schema):
        if referred_schema == "diamond_oltp":
            return BLANK_SCHEMA
        return referred_schema

    for table in Base.metadata.sorted_tables:
        schema = None if table.schema == "diamond_oltp" else table.schema
        copied_table = table.to_metadata(
            metadata,
            schema=schema,
            referred_schema_fn=referred_schema_fn,
        )
        for source_index in table.indexes:
            source_columns = tuple(column.name for column in source_index.columns)
            copied_index = next(
                index
                for index in copied_table.indexes
                if tuple(column.name for column in index.columns) == source_columns
            )
            copied_index.name = source_index.name
    return metadata


target_metadata = build_comparison_metadata()


def include_name(name, type_, parent_names):
    """Limit autogenerate to the three databases owned by Diamant ID."""
    if type_ == "schema":
        return name is None or name in MANAGED_SCHEMAS
    return True


def include_object(object_, name, type_, reflected, compare_to):
    """Keep Alembic's own version table out of application schema diffs."""
    return not (type_ == "table" and name == "alembic_version")


def run_migrations_offline() -> None:
    """Generate SQL only; no database connection or mutation is performed."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        include_schemas=True,
        include_name=include_name,
        include_object=include_object,
        version_table_schema="diamond_oltp",
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations after the non-destructive MariaDB database bootstrap."""
    # Pass URL directly:
    # `str(URL)` masks its password as `***` and must never configure a real
    # connection.
    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            include_object=include_object,
            version_table_schema="diamond_oltp",
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
