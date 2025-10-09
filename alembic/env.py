"""Alembic migration environment configuration."""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import settings
from app.core.config import settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with our DATABASE_URL from settings
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# Import all models here so Alembic can detect them
# This is critical for autogenerate to work
from app.clients.models import Client  # noqa: E402, F401
from app.users.models import (  # noqa: E402, F401
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)

# TODO: Uncomment as you create these models
# from app.catalog.models import Item, Package, PackageItem, Room  # noqa: E402, F401
# from app.sessions.models import (  # noqa: E402, F401
#     Session,
#     SessionDetail,
#     SessionPayment,
#     SessionPhotographer,
#     SessionStatusHistory,
# )

# Set target metadata for autogenerate support
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        version_table_schema='studio',
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with the provided connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema='studio',
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    In this scenario we need to create an async Engine
    and associate a connection with the context.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
