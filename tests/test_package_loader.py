
"""Pruebas para la carga de paquetes JSON."""

import json

import pytest

from saberia.content.package_loader import PackageLoadError, load_package


def valid_package():
    """Construye un paquete mínimo válido para las pruebas."""
    return {
        "schema_version": "1.0",
        "package": {
            "package_uid": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Ciencias naturales",
            "version": "1.0.0",
        },
        "source": {
            "name": "SABERIA - Banco interno de preguntas",
            "license_code": "PROPRIETARY_INTERNAL",
            "attribution_text": "Contenido propio del proyecto SABERIA",
        },
        "taxonomy": {
            "categories": [
                {
                    "code": "CN",
                    "name": "Ciencias naturales",
                    "topics": [
                        {
                            "code": "BIO",
                            "name": "Biología",
                            "competencies": [
                                {
                                    "code": "BIO-01",
                                    "name": "Comprensión de los seres vivos",
                                }
                            ],
                        }
                    ],
                }
            ]
        },
        "questions": [
            {
                "external_id": "CN-0001",
                "category_code": "CN",
                "topic_code": "BIO",
                "competency_code": "BIO-01",
                "language": "es",
                "qtype": "single_choice",
                "prompt": "¿Cuál de estos animales es un mamífero?",
                "explanation": "Los mamíferos alimentan a sus crías con leche.",
                "age_min": 4,
                "age_max": 6,
                "difficulty": 1,
                "origin": "own",
                "options": [
                    {"text": "Perro", "is_correct": True},
                    {"text": "Rana", "is_correct": False},
                    {"text": "Pez", "is_correct": False},
                ],
            }
        ],
    }


def test_loads_valid_json_package(tmp_path):
    """Carga correctamente un paquete JSON válido."""
    package = valid_package()
    file_path = tmp_path / "paquete.json"
    file_path.write_text(
        json.dumps(package, ensure_ascii=False),
        encoding="utf-8",
    )

    result = load_package(file_path)

    assert result == package


def test_rejects_invalid_json(tmp_path):
    """Rechaza archivos cuyo contenido no es JSON válido."""
    file_path = tmp_path / "paquete.json"
    file_path.write_text('{"package": ', encoding="utf-8")

    with pytest.raises(PackageLoadError, match="JSON válido"):
        load_package(file_path)


def test_rejects_package_with_validation_errors(tmp_path):
    """Rechaza paquetes JSON que incumplen el contrato."""
    package = valid_package()
    package["questions"][0]["difficulty"] = 10

    file_path = tmp_path / "paquete.json"
    file_path.write_text(
        json.dumps(package, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(PackageLoadError, match="errores de validación"):
        load_package(file_path)


def test_rejects_missing_file(tmp_path):
    """Informa cuando el archivo solicitado no existe."""
    file_path = tmp_path / "inexistente.json"

    with pytest.raises(FileNotFoundError):
        load_package(file_path)
