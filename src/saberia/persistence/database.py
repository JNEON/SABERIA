"""Conexión con MySQL/MariaDB y gestión de sesiones de SABERIA.

SQLAlchemy se importa de forma diferida cuando es posible para que las
comprobaciones básicas no exijan tener instaladas las librerías de BD.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

from saberia.config.settings import Settings

logger = logging.getLogger(__name__)

MIN_MYSQL_VERSION: tuple[int, int, int] = (8, 0, 16)
MIN_MARIADB_VERSION: tuple[int, int, int] = (10, 2, 1)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")

_AUTH_ERRORS = {1044, 1045}
_UNKNOWN_DATABASE = 1049
_UNREACHABLE_ERRORS = {2002, 2003, 2006, 2013}


class ErrorKind(Enum):
    DRIVER_MISSING = "driver_missing"
    SERVER_UNREACHABLE = "server_unreachable"
    AUTH_FAILED = "auth_failed"
    UNKNOWN_DATABASE = "unknown_database"
    UNSUPPORTED_SERVER = "unsupported_server"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConnectionResult:
    """Resultado de la comprobación de conexión."""

    ok: bool
    message: str
    server_version: str | None = None
    error_kind: ErrorKind | None = None


def parse_mysql_version(raw: str) -> tuple[int, int, int] | None:
    """Extrae la versión numérica de MySQL o MariaDB."""
    match = _VERSION_RE.match(raw.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def build_url(settings: Settings) -> Any:
    """Construye la URL SQLAlchemy sin exponer la contraseña."""
    from sqlalchemy.engine import URL

    return URL.create(
        "mysql+pymysql",
        username=settings.db_user,
        password=settings.db_password or None,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={"charset": "utf8mb4"},
    )


def create_engine_from_settings(settings: Settings) -> Any:
    """Crea un motor SQLAlchemy con la configuración de SABERIA."""
    from sqlalchemy import create_engine

    return create_engine(
        build_url(settings),
        connect_args={"connect_timeout": settings.db_connect_timeout},
        pool_pre_ping=True,
    )


def create_session_factory(engine: Any) -> Any:
    """Crea una fábrica de sesiones asociada al motor o conexión recibida."""
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(
        bind=engine,
        autoflush=True,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(session_factory: Any) -> Iterator[Any]:
    """Administra una sesión y su transacción.

    Confirma si el bloque termina correctamente.
    Revierte si ocurre una excepción.
    Cierra siempre la sesión.
    """
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def fetch_server_version(settings: Settings) -> str:
    """Abre una conexión de prueba y devuelve SELECT VERSION()."""
    from sqlalchemy import text

    engine = create_engine_from_settings(settings)

    try:
        with engine.connect() as connection:
            return str(connection.execute(text("SELECT VERSION()")).scalar_one())
    finally:
        engine.dispose()


def check_connection(
    settings: Settings,
    fetch_version: Callable[[Settings], str] | None = None,
) -> ConnectionResult:
    """Comprueba conexión, existencia de BD y versión compatible."""
    fetch = fetch_version or fetch_server_version

    try:
        raw_version = fetch(settings)
    except ImportError as exc:
        logger.debug("Dependencia ausente", exc_info=True)
        missing = exc.name or "una dependencia de base de datos"
        return ConnectionResult(
            ok=False,
            message=f'Falta {missing}. Instala el proyecto con: pip install -e ".[dev]"',
            error_kind=ErrorKind.DRIVER_MISSING,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Fallo de conexión", exc_info=True)
        return _failure_from_exception(exc, settings)

    return _evaluate_version(raw_version)


def _mysql_error_code(exc: BaseException) -> int | None:
    original = getattr(exc, "orig", exc)
    args = getattr(original, "args", ())

    if args and isinstance(args[0], int):
        return args[0]

    return None


def _failure_from_exception(
    exc: BaseException,
    settings: Settings,
) -> ConnectionResult:
    code = _mysql_error_code(exc)
    where = f"{settings.db_host}:{settings.db_port}"

    if code in _AUTH_ERRORS:
        return ConnectionResult(
            ok=False,
            message=(
                f"Acceso denegado para el usuario '{settings.db_user}' "
                f"en la base '{settings.db_name}'. Revisa las variables "
                "SABERIA_DB_USER, SABERIA_DB_PASSWORD y los permisos."
            ),
            error_kind=ErrorKind.AUTH_FAILED,
        )

    if code == _UNKNOWN_DATABASE:
        return ConnectionResult(
            ok=False,
            message=(
                f"La base de datos '{settings.db_name}' no existe. "
                "Créala siguiendo las instrucciones del README."
            ),
            error_kind=ErrorKind.UNKNOWN_DATABASE,
        )

    if code in _UNREACHABLE_ERRORS or isinstance(exc, OSError):
        return ConnectionResult(
            ok=False,
            message=(
                f"No se pudo conectar con MySQL/MariaDB en {where}. "
                "Revisa el servicio y las variables SABERIA_DB_HOST y "
                "SABERIA_DB_PORT."
            ),
            error_kind=ErrorKind.SERVER_UNREACHABLE,
        )

    return ConnectionResult(
        ok=False,
        message=f"Error inesperado al conectar ({type(exc).__name__}).",
        error_kind=ErrorKind.UNKNOWN,
    )


def _evaluate_version(raw_version: str) -> ConnectionResult:
    """Valida la versión mínima de MySQL o MariaDB."""
    is_mariadb = "mariadb" in raw_version.lower()

    if is_mariadb:
        required_version = MIN_MARIADB_VERSION
        server_name = "MariaDB"
    else:
        required_version = MIN_MYSQL_VERSION
        server_name = "MySQL"

    required = ".".join(str(part) for part in required_version)
    parsed = parse_mysql_version(raw_version)

    if parsed is None:
        return ConnectionResult(
            ok=False,
            message=f"No se pudo interpretar la versión del servidor ('{raw_version}').",
            server_version=raw_version,
            error_kind=ErrorKind.UNSUPPORTED_SERVER,
        )

    if parsed < required_version:
        return ConnectionResult(
            ok=False,
            message=(
                f"{server_name} {raw_version} es demasiado antiguo: "
                f"se requiere {required} o superior."
            ),
            server_version=raw_version,
            error_kind=ErrorKind.UNSUPPORTED_SERVER,
        )

    return ConnectionResult(
        ok=True,
        message=f"Conexión correcta. Servidor {server_name} {raw_version}.",
        server_version=raw_version,
    )
