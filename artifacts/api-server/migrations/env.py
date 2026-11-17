"""Alembic environment.

Uses its own engine, without the application's append-only guards, because migrations
are the one place where table structure is allowed to change. Rules for every revision:
only the `public` schema, and no triggers, functions or grants, since the published
database receives none of those.
"""

from __future__ import annotations

import logging

from alembic import context
from sqlalchemy import create_engine, pool

from stai.core.config import load_settings, normalise_database_url
from stai.db import models  # noqa: F401  (registers every table on the metadata)
from stai.db.base import Base, UtcDateTime

config = context.config
target_metadata = Base.metadata

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def _render_item(type_: str, obj: object, autogen_context: object) -> str | bool:
    """Keep revisions free of application imports: write the plain column type."""
    if type_ == "type" and isinstance(obj, UtcDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def _database_url() -> str:
    # Tests point migrations at their own database through this attribute.
    override = config.attributes.get("database_url")
    if override:
        return normalise_database_url(str(override))

    settings = load_settings()
    if settings.is_published:
        raise RuntimeError(
            "Migrations run in development only. The published database gets its "
            "structure from Replit's Publish step."
        )
    url = settings.sqlalchemy_url
    if url is None:
        raise RuntimeError("DATABASE_URL is not set, so there is no database to migrate.")
    return url


def run_migrations_offline() -> None:
    """Print the SQL instead of running it: `alembic upgrade head --sql`."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool, hide_parameters=True)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
                render_item=_render_item,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
