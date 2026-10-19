from logging.config import fileConfig
from pathlib import Path
import os
import sys

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool


# Project root:
# capstoneproject1/
project_root = Path(__file__).resolve().parents[1]

# Ensure imports such as "from src.app..." work
sys.path.insert(0, str(project_root))

# Load capstoneproject1/.env
load_dotenv(project_root / ".env")


# Import Base and models after adding project root to sys.path
from src.app.db.session import Base
from src.app.db import models  # noqa: F401


config = context.config


# Read the synchronous Alembic URL
database_url = os.getenv("ALEMBIC_DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "ALEMBIC_DATABASE_URL is not set in the project .env file"
    )


# Resolve the relative certificate path
ca_cert_relative = os.getenv("ALEMBIC_CA_CERT", "certs/ca.pem")
ca_cert_path = project_root / ca_cert_relative

if not ca_cert_path.exists():
    raise RuntimeError(
        f"Aiven CA certificate was not found: {ca_cert_path}"
    )


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations using a live PostgreSQL connection.
    """

    connectable = create_engine(
        database_url,
        connect_args={
            "sslmode": "verify-full",
            "sslrootcert": str(ca_cert_path),
        },
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()