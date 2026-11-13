"""Pruebas unitarias de las entidades del dominio de SABERIA."""

import pytest

from saberia.domain.entities import (
    AnswerRecord,
    GameSession,
    Player,
    Question,
    QuestionOption,
)
from saberia.domain.enums import (
    AgeGroup,
    AnswerStatus,
    Difficulty,
    QuestionType,
)


def make_question(**overrides):
    """Construye una pregunta válida para reutilizarla en las pruebas."""
    data = {
        "question_id": "Q001",
        "statement": "¿Cuánto es 5 + 3?",
        "competency_id": "CALC",
        "age_min": 7,
        "age_max": 12,
        "difficulty": Difficulty.BASIC,
        "question_type": QuestionType.SINGLE_CHOICE,
        "options": (
            QuestionOption("A", "6"),
            QuestionOption("B", "8"),
            QuestionOption("C", "9"),
        ),
        "correct_option_id": "B",
    }
    data.update(overrides)
    return Question(**data)


# --------------------------------------------------
# PARTICIPANTES
# --------------------------------------------------


def test_player_creation():
    player = Player("P001", "Sofia", 9)

    assert player.player_id == "P001"
    assert player.name == "Sofia"
    assert player.age == 9
    assert player.age_group == AgeGroup.AGE_7_9


def test_player_rejects_age_below_four():
    with pytest.raises(ValueError):
        Player("P001", "Sofia", 3)


def test_player_rejects_empty_name():
    with pytest.raises(ValueError):
        Player("P001", " ", 9)


def test_player_rejects_non_integer_age():
    with pytest.raises(ValueError):
        Player("P001", "Sofia", 9.5)


# --------------------------------------------------
# PREGUNTAS
# --------------------------------------------------


def test_question_creation():
    question = make_question()

    assert question.question_id == "Q001"
    assert question.correct_option_id == "B"
    assert len(question.options) == 3


def test_question_allowed_age():
    question = make_question()

    assert question.is_allowed_for_age(7)
    assert question.is_allowed_for_age(9)
    assert question.is_allowed_for_age(12)
    assert not question.is_allowed_for_age(6)
    assert not question.is_allowed_for_age(13)


def test_question_with_open_age_range():
    question = make_question(age_min=18, age_max=None)

    assert question.is_allowed_for_age(18)
    assert question.is_allowed_for_age(35)
    assert not question.is_allowed_for_age(17)


def test_question_rejects_missing_correct_option():
    with pytest.raises(ValueError):
        make_question(correct_option_id="Z")


def test_question_rejects_duplicate_options():
    with pytest.raises(ValueError):
        make_question(
            options=(
                QuestionOption("A", "6"),
                QuestionOption("A", "8"),
            )
        )


def test_true_false_question_requires_two_options():
    with pytest.raises(ValueError):
        make_question(
            question_type=QuestionType.TRUE_FALSE,
            options=(
                QuestionOption("A", "Verdadero"),
                QuestionOption("B", "Falso"),
                QuestionOption("C", "No sé"),
            ),
        )


# --------------------------------------------------
# REGISTRO DE RESPUESTAS
# --------------------------------------------------


def test_correct_answer_record():
    record = AnswerRecord(
        player_id="P001",
        question_id="Q001",
        status=AnswerStatus.CORRECT,
        selected_option_id="B",
        elapsed_seconds=8.5,
    )

    assert record.status == AnswerStatus.CORRECT
    assert record.selected_option_id == "B"
    assert record.elapsed_seconds == 8.5
    assert record.used_hint is False


def test_answer_record_with_hint():
    record = AnswerRecord(
        player_id="P001",
        question_id="Q001",
        status=AnswerStatus.CORRECT,
        selected_option_id="B",
        elapsed_seconds=10,
        used_hint=True,
    )

    assert record.used_hint is True


def test_skipped_answer_has_no_selected_option():
    record = AnswerRecord(
        player_id="P001",
        question_id="Q001",
        status=AnswerStatus.SKIPPED,
        selected_option_id=None,
        elapsed_seconds=5,
    )

    assert record.status == AnswerStatus.SKIPPED
    assert record.selected_option_id is None


def test_timeout_answer_has_no_selected_option():
    record = AnswerRecord(
        player_id="P001",
        question_id="Q001",
        status=AnswerStatus.TIMEOUT,
        selected_option_id=None,
        elapsed_seconds=15,
    )

    assert record.status == AnswerStatus.TIMEOUT


def test_answer_record_rejects_negative_time():
    with pytest.raises(ValueError):
        AnswerRecord(
            player_id="P001",
            question_id="Q001",
            status=AnswerStatus.CORRECT,
            selected_option_id="B",
            elapsed_seconds=-1,
        )


def test_answer_record_requires_selected_option():
    with pytest.raises(ValueError):
        AnswerRecord(
            player_id="P001",
            question_id="Q001",
            status=AnswerStatus.CORRECT,
            selected_option_id=None,
            elapsed_seconds=5,
        )


# --------------------------------------------------
# PARTIDAS
# --------------------------------------------------


def test_game_session_creation():
    game = GameSession(
        session_id="G001",
        player_ids=("P001", "P002"),
    )

    assert game.session_id == "G001"
    assert len(game.player_ids) == 2
    assert game.is_finished is False


def test_game_session_accepts_up_to_eight_players():
    game = GameSession(
        session_id="G001",
        player_ids=tuple(f"P{i:03}" for i in range(1, 9)),
    )

    assert len(game.player_ids) == 8


def test_game_session_rejects_one_player():
    with pytest.raises(ValueError):
        GameSession("G001", ("P001",))


def test_game_session_rejects_duplicate_players():
    with pytest.raises(ValueError):
        GameSession("G001", ("P001", "P001"))


def test_game_session_registers_question():
    game = GameSession("G001", ("P001", "P002"))

    game.register_question("Q001")

    assert "Q001" in game.asked_question_ids


def test_game_session_rejects_repeated_question():
    game = GameSession("G001", ("P001", "P002"))

    game.register_question("Q001")

    with pytest.raises(ValueError):
        game.register_question("Q001")
