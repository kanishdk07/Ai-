from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import sys
import os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.database import Base
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Use SQLite or PostgreSQL sync URL for Alembic autogeneration
url = settings.DATABASE_URL
if "postgresql" in url:
    # Use sqlite for autogenerating schema migrations if postgresql driver not installed locally
    url = "sqlite:///highway_accident_detection.db"
elif "sqlite+aiosqlite://" in url:
    url = url.replace("sqlite+aiosqlite://", "sqlite://")

config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=lambda obj, name, type_, reflected, compare_to: True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=lambda obj, name, type_, reflected, compare_to: True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
