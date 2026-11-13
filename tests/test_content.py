
"""Pruebas automatizadas para el validador de paquetes SABERIA."""

from copy import deepcopy

import pytest

from saberia.content.validator import validate_package


def valid_package() -> dict:
    """Construye un paquete mínimo válido para las pruebas."""
    return {
        "schema_version": "1.0",
        "package": {
            "package_uid": "550e8400-e29b-41d4-a716-446655440000",
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
                            "code": "CN-BIO",
                            "name": "Biología",
                            "competencies": [
                                {
                                    "code": "CN-BIO-01",
                                    "name": "Reconocer los seres vivos",
                                    "description": "Identificación de características.",
                                }
                            ],
                        },
                        {
                            "code": "CN-ECO",
                            "name": "Ecología",
                            "competencies": [
                                {
                                    "code": "CN-BIO-01",
                                    "name": "Reconocer relaciones ecológicas",
                                }
                            ],
                        },
                    ],
                }
            ]
        },
        "questions": [
            {
                "external_id": "CN-0001",
                "category_code": "CN",
                "topic_code": "CN-BIO",
                "competency_code": "CN-BIO-01",
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
                    {"text": "Mariposa", "is_correct": False},
                ],
            }
        ],
    }


def test_accepts_valid_package():
    """Un paquete correctamente estructurado no debe generar errores."""
    errors = validate_package(valid_package())

    assert errors == []


def test_rejects_non_object_package():
    """El contenido principal debe ser un objeto."""
    errors = validate_package(None)

    assert errors == [
        "El contenido del paquete debe ser un objeto JSON."
    ]


def test_rejects_invalid_package_uuid():
    """El identificador del paquete debe ser un UUID válido."""
    data = valid_package()
    data["package"]["package_uid"] = "identificador-invalido"

    errors = validate_package(data)

    assert any("package_uid" in error for error in errors)


def test_rejects_invalid_package_version():
    """La versión debe utilizar el formato X.Y.Z."""
    data = valid_package()
    data["package"]["version"] = "1.0"

    errors = validate_package(data)

    assert any("package.version" in error for error in errors)


def test_rejects_question_with_missing_competency_path():
    """La ruta de categoría, tema y competencia debe existir."""
    data = valid_package()
    data["questions"][0]["topic_code"] = "CN-QUIM"

    errors = validate_package(data)

    assert any(
        "ruta categoría/tema/competencia" in error
        for error in errors
    )


def test_allows_same_competency_code_in_different_topics():
    """Un código de competencia puede repetirse en temas distintos."""
    data = valid_package()
    question = data["questions"][0]
    question["topic_code"] = "CN-ECO"

    errors = validate_package(data)

    assert errors == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age_min", 3),
        ("age_min", 256),
        ("age_min", True),
        ("age_max", 2),
        ("age_max", 256),
        ("age_max", False),
    ],
)
def test_rejects_invalid_age_values(field, value):
    """Las edades deben ser enteros válidos y no booleanos."""
    data = valid_package()
    data["questions"][0][field] = value

    errors = validate_package(data)

    assert any(f".{field}:" in error for error in errors)


def test_rejects_age_max_lower_than_age_min():
    """La edad máxima no puede ser inferior a la mínima."""
    data = valid_package()
    data["questions"][0]["age_min"] = 10
    data["questions"][0]["age_max"] = 8

    errors = validate_package(data)

    assert any("age_max" in error for error in errors)


@pytest.mark.parametrize("difficulty", [0, 6, True, "3"])
def test_rejects_invalid_difficulty(difficulty):
    """La dificultad debe ser un entero entre 1 y 5."""
    data = valid_package()
    data["questions"][0]["difficulty"] = difficulty

    errors = validate_package(data)

    assert any("difficulty" in error for error in errors)


def test_rejects_question_without_correct_option():
    """Cada pregunta debe tener exactamente una opción correcta."""
    data = valid_package()

    for option in data["questions"][0]["options"]:
        option["is_correct"] = False

    errors = validate_package(data)

    assert any("exactamente una respuesta correcta" in error for error in errors)


def test_rejects_question_with_multiple_correct_options():
    """No se permiten dos respuestas correctas."""
    data = valid_package()
    data["questions"][0]["options"][1]["is_correct"] = True

    errors = validate_package(data)

    assert any("exactamente una respuesta correcta" in error for error in errors)


def test_rejects_true_false_with_more_than_two_options():
    """Las preguntas verdadero/falso deben tener exactamente dos opciones."""
    data = valid_package()
    question = data["questions"][0]
    question["qtype"] = "true_false"
    question["options"].append(
        {"text": "Otra opción", "is_correct": False}
    )

    errors = validate_package(data)

    assert any(
        "true_false debe tener exactamente dos opciones" in error
        for error in errors
    )


def test_rejects_duplicate_external_ids():
    """Los identificadores de preguntas no deben repetirse."""
    data = valid_package()
    duplicate = deepcopy(data["questions"][0])
    data["questions"].append(duplicate)

    errors = validate_package(data)

    assert any("código duplicado" in error for error in errors)


def test_rejects_description_over_255_characters():
    """Las descripciones de temas y competencias tienen límite de 255."""
    data = valid_package()
    data["taxonomy"]["categories"][0]["topics"][0]["description"] = (
        "A" * 256
    )

    errors = validate_package(data)

    assert any("description" in error for error in errors)


def test_rejects_question_without_options():
    """Una pregunta debe tener entre dos y seis opciones."""
    data = valid_package()
    data["questions"][0]["options"] = []

    errors = validate_package(data)

    assert any("entre 2 y 6 opciones" in error for error in errors)
