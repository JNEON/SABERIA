"""Reglas de negocio fundamentales de SABERIA."""

from collections.abc import Iterable
from dataclasses import dataclass

from saberia.domain.entities import AnswerRecord, Player, Question
from saberia.domain.enums import AnswerStatus

# Configuración de las reglas educativas.
POINTS_FOR_CORRECT_ANSWER = 1
POINTS_FOR_OTHER_RESULTS = 0

MIN_COMPETENCY_ANSWERS = 5
STRENGTH_THRESHOLD = 80.0
IMPROVEMENT_THRESHOLD = 50.0


@dataclass(frozen=True)
class CompetencyAssessment:
    """Resultado de la evaluación del desempeño en una competencia."""

    evaluable_answers: int
    correct_answers: int
    percentage: float | None
    level: str


def ensure_question_allowed(player: Player, question: Question) -> None:
    """Impide asignar preguntas fuera del rango de edad del participante."""
    if not question.is_allowed_for_age(player.age):
        raise ValueError(
            f"La pregunta {question.question_id} no está permitida "
            f"para un participante de {player.age} años."
        )


def evaluate_answer(
    question: Question,
    selected_option_id: str,
) -> AnswerStatus:
    """Determina si la opción seleccionada es correcta o incorrecta."""
    valid_options = {option.option_id for option in question.options}

    if selected_option_id not in valid_options:
        raise ValueError("La opción seleccionada no pertenece a la pregunta.")

    if selected_option_id == question.correct_option_id:
        return AnswerStatus.CORRECT

    return AnswerStatus.INCORRECT


def calculate_score(status: AnswerStatus) -> int:
    """Calcula los puntos obtenidos según el resultado de la pregunta."""
    if not isinstance(status, AnswerStatus):
        raise ValueError("El estado de la respuesta no es válido.")

    if status == AnswerStatus.CORRECT:
        return POINTS_FOR_CORRECT_ANSWER

    return POINTS_FOR_OTHER_RESULTS


def is_evaluable_answer(record: AnswerRecord) -> bool:
    """Indica si una respuesta puede utilizarse para evaluar competencias."""
    return record.status in (AnswerStatus.CORRECT, AnswerStatus.INCORRECT) and not record.used_hint


def assess_competency(
    records: Iterable[AnswerRecord],
) -> CompetencyAssessment:
    """Evalúa el desempeño de una competencia según sus respuestas registradas.

    Los registros recibidos deben corresponder a una misma competencia.
    Las respuestas omitidas, agotadas o contestadas con pista se excluyen.
    """
    evaluable = [record for record in records if is_evaluable_answer(record)]

    total = len(evaluable)
    correct = sum(record.status == AnswerStatus.CORRECT for record in evaluable)

    if total < MIN_COMPETENCY_ANSWERS:
        return CompetencyAssessment(
            evaluable_answers=total,
            correct_answers=correct,
            percentage=None,
            level="insufficient_data",
        )

    percentage = (correct / total) * 100

    if percentage >= STRENGTH_THRESHOLD:
        level = "strength"
    elif percentage <= IMPROVEMENT_THRESHOLD:
        level = "needs_improvement"
    else:
        level = "developing"

    return CompetencyAssessment(
        evaluable_answers=total,
        correct_answers=correct,
        percentage=round(percentage, 2),
        level=level,
    )
