
"""Carga y validación de paquetes JSON de preguntas de SABERIA."""

import json
from pathlib import Path
from typing import Any

from .validator import validate_package


class PackageLoadError(ValueError):
    """Error al leer o validar un paquete de preguntas."""


def load_package(path: str | Path) -> dict[str, Any]:
    """Lee un paquete JSON, valida su estructura y devuelve sus datos.

    Esta función no realiza operaciones sobre la base de datos.
    """
    package_path = Path(path)

    try:
        content = package_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PackageLoadError(
            f"El archivo '{package_path}' no tiene una codificación UTF-8 válida."
        ) from exc

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise PackageLoadError(
            f"El archivo '{package_path}' no contiene JSON válido. "
            f"Línea {exc.lineno}, columna {exc.colno}: {exc.msg}"
        ) from exc

    errors = validate_package(data)

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise PackageLoadError(
            f"El paquete '{package_path.name}' tiene errores de validación:\n"
            f"{details}"
        )

    if not isinstance(data, dict):
        raise PackageLoadError(
            "El contenido del paquete debe ser un objeto JSON."
        )

    return data
