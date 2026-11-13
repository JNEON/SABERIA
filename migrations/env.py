"""Configuración de Alembic para las migraciones de SABERIA."""

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

# Importar todos los modelos para registrarlos en Base.metadata.
import saberia.persistence.models  # noqa: F401
from saberia.config.settings import load_settings
from saberia.persistence.base import Base
from saberia.persistence.database import build_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Directorio raíz del proyecto.
PROJECT_ROOT = (
    Path(config.config_file_name).resolve().parent if config.config_file_name else Path.cwd()
)

# Alembic solo debe modificar la base de datos de SABERIA.
EXPECTED_DATABASE = "saberiadb"


def get_database_configuration():
    """Carga la configuración y construye la URL de conexión."""

    settings = load_settings(
        env_file=PROJECT_ROOT / ".env",
    )

    if settings.db_name != EXPECTED_DATABASE:
        raise RuntimeError(
            "Migraciones canceladas: Alembic solo puede operar "
            f"sobre la base de datos '{EXPECTED_DATABASE}'."
        )

    return settings, build_url(settings)


# Metadatos de los 12 modelos ORM.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL de migraciones sin establecer conexión con el servidor."""

    _, database_url = get_database_configuration()

    context.configure(
        url=database_url.render_as_string(hide_password=True),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones mediante una conexión real."""

    settings, database_url = get_database_configuration()

    connectable = create_engine(
        database_url,
        connect_args={
            "connect_timeout": settings.db_connect_timeout,
        },
        poolclass=pool.NullPool,
        pool_pre_ping=True,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
