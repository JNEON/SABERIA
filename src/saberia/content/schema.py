
"""Contrato de datos para los paquetes de preguntas de SABERIA."""

from typing import Literal, NotRequired, TypedDict

SCHEMA_VERSION = "1.0"

QUESTION_TYPES = ("single_choice", "true_false")

QUESTION_ORIGINS = ("own", "open_source", "ai_assisted")

QUESTION_STATUSES = ("draft", "validated", "published", "retired")

DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 5

AGE_MIN = 4

# Límites alineados con los modelos ORM.
FIELD_LIMITS = {
    "package_name": 120,
    "package_version": 20,
    "source_name": 120,
    "license_code": 60,
    "license_url": 255,
    "attribution_text": 500,
    "source_url": 255,
    "category_code": 40,
    "category_name": 80,
    "topic_code": 60,
    "topic_description": 255,
    "competency_description": 255,
    "topic_name": 100,
    "competency_code": 60,
    "competency_name": 100,
    "external_id": 64,
    "language": 8,
    "qtype": 16,
    "prompt": 500,
    "explanation": 1000,
    "media_path": 255,
    "origin": 16,
    "option_text": 255,
}


class PackageMetadata(TypedDict):
    """Identificación y versión del paquete."""

    package_uid: str
    name: str
    version: str


class SourceMetadata(TypedDict):
    """Procedencia y condiciones de uso del contenido."""

    name: str
    license_code: str
    license_url: NotRequired[str | None]
    attribution_text: NotRequired[str | None]
    url: NotRequired[str | None]


class CompetencyDefinition(TypedDict):
    """Definición de una competencia."""

    code: str
    name: str
    description: NotRequired[str | None]


class TopicDefinition(TypedDict):
    """Definición de un tema y sus competencias."""

    code: str
    name: str
    competencies: list[CompetencyDefinition]
    description: NotRequired[str | None]


class CategoryDefinition(TypedDict):
    """Definición de una categoría y sus temas."""

    code: str
    name: str
    topics: list[TopicDefinition]


class TaxonomyDefinition(TypedDict):
    """Taxonomía académica incluida en el paquete."""

    categories: list[CategoryDefinition]


class QuestionOptionData(TypedDict):
    """Opción de respuesta de una pregunta."""

    text: str
    is_correct: bool


class QuestionData(TypedDict):
    """Contenido de una pregunta."""

    external_id: str
    category_code: str
    topic_code: str
    competency_code: str
    language: str
    qtype: Literal["single_choice", "true_false"]
    prompt: str
    explanation: str
    age_min: int
    age_max: int | None
    difficulty: int
    origin: Literal["own", "open_source", "ai_assisted"]
    options: list[QuestionOptionData]
    media_path: NotRequired[str | None]


class QuestionPackageData(TypedDict):
    """Estructura completa de un paquete importable."""

    schema_version: str
    package: PackageMetadata
    source: SourceMetadata
    taxonomy: TaxonomyDefinition
    questions: list[QuestionData]
