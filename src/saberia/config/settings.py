"""Carga y validación de la configuración de SABERIA.

Orden de prioridad (de mayor a menor):

1. Variables de entorno con prefijo ``SABERIA_``.
2. Archivo ``.env`` (opcional) en el directorio desde el que se ejecuta la aplicación.
3. Valores por defecto.

Ningún mensaje de error ni ``repr`` incluye la contraseña de la base de datos.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

ENV_PREFIX = "SABERIA_"
DEFAULT_ENV_FILE = Path(".env")

_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")


class SettingsError(ValueError):
    """La configuración es inválida. El mensaje nunca contiene contraseñas."""


@dataclass(frozen=True)
class Settings:
    """Configuración de conexión a MySQL (única configuración de esta fase)."""

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "saberia_app"
    db_password: str = field(default="", repr=False)
    db_name: str = "saberia"
    db_connect_timeout: int = 5


def parse_env_file(path: Path) -> dict[str, str]:
    """Lee un archivo ``.env`` sencillo (``CLAVE=valor``). Si no existe, devuelve ``{}``.

    Admite comentarios con ``#``, el prefijo ``export`` y valores entre comillas
    simples o dobles. En valores sin comillas, `` #`` inicia un comentario.
    """
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, separator, value = line.partition("=")
        if not separator:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def load_settings(
    env: Mapping[str, str] | None = None,
    env_file: Path | str | None = DEFAULT_ENV_FILE,
) -> Settings:
    """Construye la configuración o lanza ``SettingsError`` con todos los problemas.

    ``env`` permite inyectar un entorno (por defecto ``os.environ``) y
    ``env_file=None`` desactiva la lectura del archivo ``.env``.
    """
    merged: dict[str, str] = {}
    if env_file is not None:
        merged.update(parse_env_file(Path(env_file)))
    source = os.environ if env is None else env
    merged.update({key: value for key, value in source.items() if key.startswith(ENV_PREFIX)})

    defaults = Settings()
    errors: list[str] = []

    def read_text(name: str, default: str) -> str:
        key = ENV_PREFIX + name
        value = merged.get(key)
        if value is None:
            return default
        value = value.strip()
        if not value:
            errors.append(f"{key} no puede estar vacío.")
            return default
        return value

    def read_int(name: str, default: int, minimum: int, maximum: int) -> int:
        key = ENV_PREFIX + name
        raw = merged.get(key)
        if raw is None:
            return default
        try:
            number = int(raw.strip())
        except ValueError:
            number = None
        if number is None or not minimum <= number <= maximum:
            errors.append(f"{key} debe ser un entero entre {minimum} y {maximum}.")
            return default
        return number

    host = read_text("DB_HOST", defaults.db_host)
    port = read_int("DB_PORT", defaults.db_port, 1, 65535)
    user = read_text("DB_USER", defaults.db_user)
    password = merged.get(ENV_PREFIX + "DB_PASSWORD", defaults.db_password)
    name = read_text("DB_NAME", defaults.db_name)
    if not _DB_NAME_RE.fullmatch(name):
        errors.append(
            f"{ENV_PREFIX}DB_NAME solo admite letras, números y guion bajo (máximo 64 caracteres)."
        )
    timeout = read_int("DB_CONNECT_TIMEOUT", defaults.db_connect_timeout, 1, 60)

    if errors:
        raise SettingsError("Configuración inválida:\n" + "\n".join(f"- {e}" for e in errors))

    return Settings(
        db_host=host,
        db_port=port,
        db_user=user,
        db_password=password,
        db_name=name,
        db_connect_timeout=timeout,
    )
