"""Alembic environment — raw-SQL migrations (no ORM metadata). LLD §5."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

load_dotenv(override=True)

config = context.config

# asyncpg DSN -> sync psycopg (v3) URL for Alembic's migration runner.
db_url = os.environ.get("POSTGRES_URL", "postgresql://autorag:autorag@localhost:5432/autorag")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)

config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    context.configure(url=db_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    print("run_migrations_online started", flush=True)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    print("connectable created", flush=True)
    with connectable.connect() as connection:
        print("connected to database", flush=True)
        context.configure(connection=connection, target_metadata=None)
        print("context configured", flush=True)
        with context.begin_transaction():
            print("running migrations...", flush=True)
            context.run_migrations()
            print("migrations finished", flush=True)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
