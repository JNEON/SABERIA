"""Pruebas de las reglas de negocio de SABERIA."""

import pytest

from saberia.domain.entities import AnswerRecord, Player, Question, QuestionOption
from saberia.domain.enums import AnswerStatus, Difficulty, QuestionType
from saberia.domain.rules import (
    assess_competency,
    calculate_score,
    ensure_question_allowed,
    evaluate_answer,
    is_evaluable_answer,
)


def make_question():
    return Question(
        question_id="Q001",
        statement="¿Cuánto es 5 + 3?",
        competency_id="CALC",
        age_min=7,
        age_max=12,
        difficulty=Difficulty.BASIC,
        question_type=QuestionType.SINGLE_CHOICE,
        options=(
            QuestionOption("A", "6"),
            QuestionOption("B", "8"),
            QuestionOption("C", "9"),
        ),
        correct_option_id="B",
    )


def make_record(status, used_hint=False):
    selected_option = (
        "B" if status == AnswerStatus.CORRECT else "A" if status == AnswerStatus.INCORRECT else None
    )

    return AnswerRecord(
        player_id="P001",
        question_id="Q001",
        status=status,
        selected_option_id=selected_option,
        elapsed_seconds=5,
        used_hint=used_hint,
    )


# EDAD Y ASIGNACIÓN DE PREGUNTAS


def test_question_allowed_for_player():
    ensure_question_allowed(Player("P001", "Sofia", 9), make_question())


def test_question_rejected_for_player_outside_age_range():
    with pytest.raises(ValueError):
        ensure_question_allowed(Player("P001", "Sofia", 6), make_question())


# EVALUACIÓN DE RESPUESTAS


def test_correct_answer():
    assert evaluate_answer(make_question(), "B") == AnswerStatus.CORRECT


def test_incorrect_answer():
    assert evaluate_answer(make_question(), "A") == AnswerStatus.INCORRECT


def test_invalid_option_is_rejected():
    with pytest.raises(ValueError):
        evaluate_answer(make_question(), "Z")


# PUNTUACIÓN


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (AnswerStatus.CORRECT, 1),
        (AnswerStatus.INCORRECT, 0),
        (AnswerStatus.SKIPPED, 0),
        (AnswerStatus.TIMEOUT, 0),
    ],
)
def test_score_calculation(status, expected):
    assert calculate_score(status) == expected


# EVALUACIÓN DE COMPETENCIAS


def test_correct_answer_is_evaluable():
    assert is_evaluable_answer(make_record(AnswerStatus.CORRECT))


def test_incorrect_answer_is_evaluable():
    assert is_evaluable_answer(make_record(AnswerStatus.INCORRECT))


def test_answer_with_hint_is_not_evaluable():
    assert not is_evaluable_answer(make_record(AnswerStatus.CORRECT, used_hint=True))


def test_skipped_answer_is_not_evaluable():
    assert not is_evaluable_answer(make_record(AnswerStatus.SKIPPED))


def test_timeout_answer_is_not_evaluable():
    assert not is_evaluable_answer(make_record(AnswerStatus.TIMEOUT))


def test_competency_requires_five_evaluable_answers():
    records = [
        make_record(AnswerStatus.CORRECT),
        make_record(AnswerStatus.CORRECT),
        make_record(AnswerStatus.INCORRECT),
        make_record(AnswerStatus.CORRECT),
    ]

    result = assess_competency(records)

    assert result.evaluable_answers == 4
    assert result.percentage is None
    assert result.level == "insufficient_data"


def test_competency_classified_as_strength():
    records = [make_record(AnswerStatus.CORRECT) for _ in range(4)] + [
        make_record(AnswerStatus.INCORRECT)
    ]

    result = assess_competency(records)

    assert result.percentage == 80.0
    assert result.level == "strength"


def test_competency_classified_as_needs_improvement():
    records = [
        make_record(AnswerStatus.CORRECT),
        *[make_record(AnswerStatus.INCORRECT) for _ in range(4)],
    ]

    result = assess_competency(records)

    assert result.percentage == 20.0
    assert result.level == "needs_improvement"


def test_competency_classified_as_developing():
    records = [make_record(AnswerStatus.CORRECT) for _ in range(3)] + [
        make_record(AnswerStatus.INCORRECT) for _ in range(2)
    ]

    result = assess_competency(records)

    assert result.percentage == 60.0
    assert result.level == "developing"


def test_hint_does_not_count_toward_competency_minimum():
    records = [make_record(AnswerStatus.CORRECT) for _ in range(4)] + [
        make_record(AnswerStatus.CORRECT, used_hint=True)
    ]

    result = assess_competency(records)

    assert result.evaluable_answers == 4
    assert result.percentage is None
    assert result.level == "insufficient_data"
