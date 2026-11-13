
"""Validación estructural y semántica de paquetes de preguntas."""

import re
from collections.abc import Mapping
from uuid import UUID

from saberia.content.schema import (
    AGE_MIN,
    DIFFICULTY_MAX,
    DIFFICULTY_MIN,
    FIELD_LIMITS,
    QUESTION_ORIGINS,
    QUESTION_TYPES,
    SCHEMA_VERSION,
)

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

PACKAGE_KEYS = {
    "schema_version",
    "package",
    "source",
    "taxonomy",
    "questions",
}

PACKAGE_METADATA_KEYS = {"package_uid", "name", "version"}

SOURCE_KEYS = {
    "name",
    "license_code",
    "license_url",
    "attribution_text",
    "url",
}

TAXONOMY_KEYS = {"categories"}
CATEGORY_KEYS = {"code", "name", "topics"}
TOPIC_KEYS = {"code", "name", "competencies", "description"}
COMPETENCY_KEYS = {"code", "name", "description"}

QUESTION_KEYS = {
    "external_id",
    "category_code",
    "topic_code",
    "competency_code",
    "language",
    "qtype",
    "prompt",
    "explanation",
    "age_min",
    "age_max",
    "difficulty",
    "origin",
    "options",
    "media_path",
}

OPTION_KEYS = {"text", "is_correct"}


def _is_mapping(value: object) -> bool:
    """Comprueba si un valor es un objeto tipo diccionario."""
    return isinstance(value, Mapping)


def _check_keys(
    value: Mapping,
    required: set[str],
    allowed: set[str],
    path: str,
    errors: list[str],
) -> None:
    """Comprueba campos obligatorios y campos no reconocidos."""
    missing = required - value.keys()
    unknown = value.keys() - allowed

    for key in sorted(missing):
        errors.append(f"{path}: falta el campo obligatorio '{key}'.")

    for key in sorted(unknown):
        errors.append(f"{path}: campo no reconocido '{key}'.")



def _check_text(
    value: object,
    field: str,
    path: str,
    errors: list[str],
    *,
    required: bool = True,
) -> None:
    """Valida un campo de texto y su longitud máxima."""
    if not _is_mapping(value):
        errors.append(f"{path}: debe ser un objeto.")
        return

    # La ausencia del campo ya se informa mediante _check_keys().
    if field not in value:
        return

    field_value = value[field]

    if field_value is None and not required:
        return

    if not isinstance(field_value, str):
        errors.append(f"{path}.{field}: debe ser texto.")
        return

    if not field_value.strip():
        errors.append(f"{path}.{field}: no puede estar vacío.")
        return

    limit = FIELD_LIMITS.get(field)

    if limit is not None and len(field_value) > limit:
        errors.append(
            f"{path}.{field}: supera el máximo de {limit} caracteres."
        )

def _check_optional_text(
    value: Mapping,
    field: str,
    limit_field: str,
    path: str,
    errors: list[str],
) -> None:
    """Valida un campo de texto opcional."""
    if field not in value or value[field] is None:
        return

    if not isinstance(value[field], str):
        errors.append(f"{path}.{field}: debe ser texto o null.")
        return

    if len(value[field]) > FIELD_LIMITS[limit_field]:
        errors.append(
            f"{path}.{field}: supera el máximo de "
            f"{FIELD_LIMITS[limit_field]} caracteres."
        )


def _check_code(
    value: object,
    field: str,
    path: str,
    errors: list[str],
    max_length: int,
) -> None:
    """Valida un código identificador."""
    if not isinstance(value, str):
        errors.append(f"{path}.{field}: debe ser texto.")
        return

    if not value.strip():
        errors.append(f"{path}.{field}: no puede estar vacío.")
        return

    if len(value) > max_length:
        errors.append(
            f"{path}.{field}: supera el máximo de {max_length} caracteres."
        )


def validate_package(data: object) -> list[str]:
    """Valida un paquete completo y devuelve una lista de errores.

    Una lista vacía significa que el paquete superó estas validaciones.
    Esta función no consulta ni modifica la base de datos.
    """
    errors: list[str] = []

    if not _is_mapping(data):
        return ["El contenido del paquete debe ser un objeto JSON."]

    _check_keys(data, PACKAGE_KEYS, PACKAGE_KEYS, "paquete", errors)

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version: se esperaba '{SCHEMA_VERSION}'."
        )

    package = data.get("package")
    source = data.get("source")
    taxonomy = data.get("taxonomy")
    questions = data.get("questions")

    # Validar metadatos del paquete.
    if not _is_mapping(package):
        errors.append("package: debe ser un objeto.")
    else:
        _check_keys(
            package,
            PACKAGE_METADATA_KEYS,
            PACKAGE_METADATA_KEYS,
            "package",
            errors,
        )

        uid = package.get("package_uid")

        try:
            parsed_uid = UUID(uid) if isinstance(uid, str) else None

            if parsed_uid is None or str(parsed_uid) != uid.lower():
                errors.append(
                    "package.package_uid: debe ser un UUID válido."
                )
        except ValueError:
            errors.append(
                "package.package_uid: debe ser un UUID válido."
            )

        _check_text(package, "name", "package", errors)
        _check_text(package, "version", "package", errors)

        version = package.get("version")

        if isinstance(version, str) and not VERSION_PATTERN.fullmatch(version):
            errors.append(
                "package.version: debe utilizar el formato X.Y.Z."
            )

    # Validar procedencia.
    if not _is_mapping(source):
        errors.append("source: debe ser un objeto.")
    else:
        _check_keys(
            source,
            {"name", "license_code"},
            SOURCE_KEYS,
            "source",
            errors,
        )

        _check_text(source, "name", "source", errors)
        _check_text(source, "license_code", "source", errors)

        _check_optional_text(
            source,
            "license_url",
            "license_url",
            "source",
            errors,
        )

        _check_optional_text(
            source,
            "attribution_text",
            "attribution_text",
            "source",
            errors,
        )

        _check_optional_text(
            source,
            "url",
            "source_url",
            "source",
            errors,
        )

    # Validar taxonomía y construir índice de competencias.
    # La clave compuesta evita conflictos entre temas diferentes.
    competency_paths: dict[tuple[str, str, str], bool] = {}

    if not _is_mapping(taxonomy):
        errors.append("taxonomy: debe ser un objeto.")
    else:
        _check_keys(
            taxonomy,
            {"categories"},
            TAXONOMY_KEYS,
            "taxonomy",
            errors,
        )

        categories = taxonomy.get("categories")

        if not isinstance(categories, list) or not categories:
            errors.append(
                "taxonomy.categories: debe contener categorías."
            )
        else:
            category_codes: set[str] = set()

            for ci, category in enumerate(categories):
                cpath = f"taxonomy.categories[{ci}]"

                if not _is_mapping(category):
                    errors.append(f"{cpath}: debe ser un objeto.")
                    continue

                _check_keys(
                    category,
                    CATEGORY_KEYS,
                    CATEGORY_KEYS,
                    cpath,
                    errors,
                )

                code = category.get("code")
                _check_code(code, "code", cpath, errors, 40)

                if isinstance(code, str):
                    if code in category_codes:
                        errors.append(
                            f"{cpath}.code: categoría duplicada '{code}'."
                        )

                    category_codes.add(code)

                _check_text(category, "name", cpath, errors)

                topics = category.get("topics")

                if not isinstance(topics, list) or not topics:
                    errors.append(
                        f"{cpath}.topics: debe contener temas."
                    )
                    continue

                topic_codes: set[str] = set()

                for ti, topic in enumerate(topics):
                    tpath = f"{cpath}.topics[{ti}]"

                    if not _is_mapping(topic):
                        errors.append(f"{tpath}: debe ser un objeto.")
                        continue

                    _check_keys(
                        topic,
                        {"code", "name", "competencies"},
                        TOPIC_KEYS,
                        tpath,
                        errors,
                    )

                    topic_code = topic.get("code")

                    _check_code(
                        topic_code,
                        "code",
                        tpath,
                        errors,
                        60,
                    )

                    _check_text(topic, "name", tpath, errors)

                    _check_optional_text(
                        topic,
                        "description",
                        "topic_description",
                        tpath,
                        errors,
                    )

                    if isinstance(topic_code, str):
                        if topic_code in topic_codes:
                            errors.append(
                                f"{tpath}.code: tema duplicado "
                                f"'{topic_code}' en la categoría."
                            )

                        topic_codes.add(topic_code)

                    competencies = topic.get("competencies")

                    if (
                        not isinstance(competencies, list)
                        or not competencies
                    ):
                        errors.append(
                            f"{tpath}.competencies: "
                            "debe contener competencias."
                        )
                        continue

                    competency_codes: set[str] = set()

                    for ki, competency in enumerate(competencies):
                        kpath = f"{tpath}.competencies[{ki}]"

                        if not _is_mapping(competency):
                            errors.append(
                                f"{kpath}: debe ser un objeto."
                            )
                            continue

                        _check_keys(
                            competency,
                            {"code", "name"},
                            COMPETENCY_KEYS,
                            kpath,
                            errors,
                        )

                        competency_code = competency.get("code")

                        _check_code(
                            competency_code,
                            "code",
                            kpath,
                            errors,
                            60,
                        )

                        _check_text(
                            competency,
                            "name",
                            kpath,
                            errors,
                        )

                        _check_optional_text(
                            competency,
                            "description",
                            "competency_description",
                            kpath,
                            errors,
                        )

                        if not isinstance(competency_code, str):
                            continue

                        if competency_code in competency_codes:
                            errors.append(
                                f"{kpath}.code: competencia duplicada "
                                f"'{competency_code}' en el tema."
                            )

                        competency_codes.add(competency_code)

                        if (
                            isinstance(code, str)
                            and isinstance(topic_code, str)
                        ):
                            competency_paths[
                                (code, topic_code, competency_code)
                            ] = True

    # Validar preguntas.
    if not isinstance(questions, list) or not questions:
        errors.append(
            "questions: debe contener al menos una pregunta."
        )
        return errors

    question_codes: set[str] = set()

    for qi, question in enumerate(questions):
        qpath = f"questions[{qi}]"

        if not _is_mapping(question):
            errors.append(f"{qpath}: debe ser un objeto.")
            continue

        _check_keys(
            question,
            QUESTION_KEYS - {"media_path"},
            QUESTION_KEYS,
            qpath,
            errors,
        )

        _check_text(question, "external_id", qpath, errors)

        external_id = question.get("external_id")

        if isinstance(external_id, str):
            if external_id in question_codes:
                errors.append(
                    f"{qpath}.external_id: código duplicado "
                    f"'{external_id}'."
                )

            question_codes.add(external_id)

        for field, max_length in (
            ("category_code", 40),
            ("topic_code", 60),
            ("competency_code", 60),
        ):
            _check_code(
                question.get(field),
                field,
                qpath,
                errors,
                max_length,
            )

        _check_text(question, "language", qpath, errors)
        _check_text(question, "prompt", qpath, errors)
        _check_text(question, "explanation", qpath, errors)

        _check_optional_text(
            question,
            "media_path",
            "media_path",
            qpath,
            errors,
        )

        qtype = question.get("qtype")

        if qtype not in QUESTION_TYPES:
            errors.append(
                f"{qpath}.qtype: debe ser uno de {QUESTION_TYPES}."
            )

        origin = question.get("origin")

        if origin not in QUESTION_ORIGINS:
            errors.append(
                f"{qpath}.origin: debe ser uno de {QUESTION_ORIGINS}."
            )

        # Validar edades.
        age_min = question.get("age_min")
        age_max = question.get("age_max")

        if (
            not isinstance(age_min, int)
            or isinstance(age_min, bool)
            or age_min < AGE_MIN
            or age_min > 255
        ):
            errors.append(
                f"{qpath}.age_min: debe ser un entero entre 4 y 255."
            )

        if age_max is not None:
            if (
                not isinstance(age_max, int)
                or isinstance(age_max, bool)
                or age_max > 255
                or age_max < AGE_MIN
            ):
                errors.append(
                    f"{qpath}.age_max: debe ser null o "
                    "un entero entre 4 y 255."
                )
            elif (
                isinstance(age_min, int)
                and not isinstance(age_min, bool)
                and age_max < age_min
            ):
                errors.append(
                    f"{qpath}.age_max: no puede ser menor que age_min."
                )

        # Validar dificultad.
        difficulty = question.get("difficulty")

        if (
            not isinstance(difficulty, int)
            or isinstance(difficulty, bool)
            or not DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX
        ):
            errors.append(
                f"{qpath}.difficulty: debe ser un entero entre 1 y 5."
            )

        # Comprobar que la ruta completa de la competencia exista.
        competency_code = question.get("competency_code")
        category_code = question.get("category_code")
        topic_code = question.get("topic_code")

        if (
            isinstance(category_code, str)
            and isinstance(topic_code, str)
            and isinstance(competency_code, str)
        ):
            competency_key = (
                category_code,
                topic_code,
                competency_code,
            )

            if competency_key not in competency_paths:
                errors.append(
                    f"{qpath}: la ruta categoría/tema/competencia "
                    "no existe en la taxonomía."
                )

        # Validar opciones.
        options = question.get("options")

        if not isinstance(options, list):
            errors.append(
                f"{qpath}.options: debe ser una lista."
            )
            continue

        if not 2 <= len(options) <= 6:
            errors.append(
                f"{qpath}.options: debe contener entre 2 y 6 opciones."
            )

        correct_count = 0

        for oi, option in enumerate(options):
            opath = f"{qpath}.options[{oi}]"

            if not _is_mapping(option):
                errors.append(f"{opath}: debe ser un objeto.")
                continue

            _check_keys(
                option,
                OPTION_KEYS,
                OPTION_KEYS,
                opath,
                errors,
            )

            _check_text(option, "text", opath, errors)

            is_correct = option.get("is_correct")

            if not isinstance(is_correct, bool):
                errors.append(
                    f"{opath}.is_correct: debe ser true o false."
                )
            elif is_correct:
                correct_count += 1

        if correct_count != 1:
            errors.append(
                f"{qpath}.options: debe existir exactamente "
                "una respuesta correcta."
            )

        if qtype == "true_false" and len(options) != 2:
            errors.append(
                f"{qpath}: una pregunta true_false debe tener "
                "exactamente dos opciones."
            )

    return errors
