"""Conexión con MySQL y comprobación de entorno.

SQLAlchemy se importa de forma diferida: así este módulo (y sus pruebas) no
exigen tener instaladas las librerías de base de datos.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from saberia.config.settings import Settings

logger = logging.getLogger(__name__)

# Las restricciones CHECK del modelo de datos solo se aplican desde MySQL 8.0.16.
MIN_MYSQL_VERSION: tuple[int, int, int] = (8, 0, 16)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")

# Códigos de error de MySQL/PyMySQL.
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
    """Resultado de la comprobación. ``message`` está pensado para mostrarse al usuario."""

    ok: bool
    message: str
    server_version: str | None = None
    error_kind: ErrorKind | None = None


def parse_mysql_version(raw: str) -> tuple[int, int, int] | None:
    """Extrae (mayor, menor, parche) de cadenas como ``8.0.36-0ubuntu0.22.04.1``."""
    match = _VERSION_RE.match(raw.strip())
    if not match:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def build_url(settings: Settings) -> Any:
    """URL de SQLAlchemy para PyMySQL. La contraseña se escapa correctamente."""
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


def fetch_server_version(settings: Settings) -> str:
    """Abre una conexión de prueba y devuelve ``SELECT VERSION()``."""
    from sqlalchemy import create_engine, text

    engine = create_engine(
        build_url(settings),
        connect_args={"connect_timeout": settings.db_connect_timeout},
        pool_pre_ping=True,
    )
    try:
        with engine.connect() as connection:
            return str(connection.execute(text("SELECT VERSION()")).scalar_one())
    finally:
        engine.dispose()


def check_connection(
    settings: Settings,
    fetch_version: Callable[[Settings], str] | None = None,
) -> ConnectionResult:
    """Comprueba que MySQL responde, que existe la base de datos y que la versión es válida.

    ``fetch_version`` permite inyectar otra implementación (útil en pruebas).
    Nunca lanza excepciones por fallos de conexión: los devuelve en el resultado.
    """
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
    except Exception as exc:  # noqa: BLE001 - se traduce siempre a un resultado legible
        logger.debug("Fallo de conexión", exc_info=True)
        return _failure_from_exception(exc, settings)
    return _evaluate_version(raw_version)


def _mysql_error_code(exc: BaseException) -> int | None:
    original = getattr(exc, "orig", exc)
    args = getattr(original, "args", ())
    if args and isinstance(args[0], int):
        return args[0]
    return None


def _failure_from_exception(exc: BaseException, settings: Settings) -> ConnectionResult:
    code = _mysql_error_code(exc)
    where = f"{settings.db_host}:{settings.db_port}"

    if code in _AUTH_ERRORS:
        return ConnectionResult(
            ok=False,
            message=(
                f"Acceso denegado para el usuario '{settings.db_user}' en la base "
                f"'{settings.db_name}'. Revisa SABERIA_DB_USER, SABERIA_DB_PASSWORD y "
                "los permisos del usuario."
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
                f"No se pudo conectar con MySQL en {where}. "
                "¿Está iniciado el servicio? Revisa SABERIA_DB_HOST y SABERIA_DB_PORT."
            ),
            error_kind=ErrorKind.SERVER_UNREACHABLE,
        )
    return ConnectionResult(
        ok=False,
        message=f"Error inesperado al conectar con MySQL ({type(exc).__name__}).",
        error_kind=ErrorKind.UNKNOWN,
    )


def _evaluate_version(raw_version: str) -> ConnectionResult:
    required = ".".join(str(part) for part in MIN_MYSQL_VERSION)
    parsed = parse_mysql_version(raw_version)

    if parsed is None:
        return ConnectionResult(
            ok=False,
            message=f"No se pudo interpretar la versión del servidor ('{raw_version}').",
            server_version=raw_version,
            error_kind=ErrorKind.UNSUPPORTED_SERVER,
        )
    if "mariadb" in raw_version.lower():
        return ConnectionResult(
            ok=False,
            message=(
                f"El servidor es MariaDB ({raw_version}). SABERIA está diseñado y probado "
                f"para MySQL {required} o superior."
            ),
            server_version=raw_version,
            error_kind=ErrorKind.UNSUPPORTED_SERVER,
        )
    if parsed < MIN_MYSQL_VERSION:
        return ConnectionResult(
            ok=False,
            message=(
                f"MySQL {raw_version} es demasiado antiguo: se requiere {required} o superior "
                "(las restricciones CHECK del modelo de datos no se aplicarían)."
            ),
            server_version=raw_version,
            error_kind=ErrorKind.UNSUPPORTED_SERVER,
        )
    return ConnectionResult(
        ok=True,
        message=f"Conexión correcta. Servidor MySQL {raw_version}.",
        server_version=raw_version,
    )
