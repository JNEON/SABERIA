"""Modelos de jugadores y partidas de SABERIA."""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import (
    BIGINT,
    DATETIME,
    INTEGER,
    SMALLINT,
    TINYINT,
)
from sqlalchemy.dialects.mysql import JSON as MYSQL_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saberia.persistence.base import Base
from saberia.persistence.models.questions import Question, QuestionOption


class Player(Base):
    """Participante registrado en SABERIA."""

    __tablename__ = "players"

    __table_args__ = (
        CheckConstraint(
            """
            age_band IN (
                '4-6',
                '7-9',
                '10-12',
                '13-15',
                '16-17',
                '18+'
            )
            """,
            name="age_band_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    display_name: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    age_band: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    avatar_key: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )

    # Partidas en las que participa este jugador.
    game_players: Mapped[list["GamePlayer"]] = relationship(
        "GamePlayer",
        back_populates="player",
    )


class Game(Base):
    """Partida de SABERIA."""

    __tablename__ = "games"

    __table_args__ = (
        CheckConstraint(
            "mode IN ('roulette', 'board')",
            name="mode_valid",
        ),
        CheckConstraint(
            "play_style IN ('competitive', 'cooperative')",
            name="play_style_valid",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'finished', 'abandoned')",
            name="status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="roulette",
    )

    play_style: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="competitive",
    )

    language: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="es",
    )

    rng_seed: Mapped[int] = mapped_column(
        BIGINT,
        nullable=False,
    )

    config_json: Mapped[dict] = mapped_column(
        MYSQL_JSON,
        nullable=False,
        default=dict,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="in_progress",
    )

    started_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )

    # Participantes registrados en esta partida.
    game_players: Mapped[list["GamePlayer"]] = relationship(
        "GamePlayer",
        back_populates="game",
        order_by="GamePlayer.seat",
    )


class GamePlayer(Base):
    """Participante y configuración individual dentro de una partida."""

    __tablename__ = "game_players"

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "seat",
            name="uq_game_players_game_seat",
        ),
        UniqueConstraint(
            "game_id",
            "player_id",
            name="uq_game_players_game_player",
        ),
        UniqueConstraint(
            "game_id",
            "id",
            name="uq_game_players_game_id",
        ),
        CheckConstraint(
            "seat BETWEEN 1 AND 8",
            name="seat_valid",
        ),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name="difficulty_valid",
        ),
        CheckConstraint(
            "timer_seconds IN (10, 15, 20, 30, 45)",
            name="timer_seconds_valid",
        ),
        CheckConstraint(
            """
            age_band IN (
                '4-6',
                '7-9',
                '10-12',
                '13-15',
                '16-17',
                '18+'
            )
            """,
            name="age_band_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "games.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    player_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "players.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    seat: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    age_band: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    difficulty: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    timer_seconds: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    final_score: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    # Relaciones con la partida y el jugador.
    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="game_players",
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="game_players",
    )

    # Historial de turnos de este participante.
    turns: Mapped[list["GameTurn"]] = relationship(
        "GameTurn",
        back_populates="game_player",
        foreign_keys="[GameTurn.game_id, GameTurn.game_player_id]",
        order_by="GameTurn.turn_no",
    )


class GameTurn(Base):
    """Registro histórico de una pregunta presentada durante una partida."""

    __tablename__ = "game_turns"

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "turn_no",
            name="uq_game_turns_game_turn_no",
        ),
        ForeignKeyConstraint(
            ["game_id", "game_player_id"],
            ["game_players.game_id", "game_players.id"],
            ondelete="RESTRICT",
            name="fk_game_turns_game_player",
        ),
        ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["question_options.question_id", "question_options.id"],
            ondelete="RESTRICT",
            name="fk_game_turns_question_option",
        ),
        CheckConstraint(
            """
            outcome IN (
                'correct',
                'incorrect',
                'skipped',
                'timed_out'
            )
            """,
            name="outcome_valid",
        ),
        CheckConstraint(
            "points_awarded IN (0, 1)",
            name="points_awarded_valid",
        ),
        Index(
            "ix_game_turns_game_player_outcome",
            "game_player_id",
            "outcome",
        ),
        Index(
            "ix_game_turns_question_id",
            "question_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    game_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )

    game_player_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
    )

    turn_no: Mapped[int] = mapped_column(
        SMALLINT(unsigned=True),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    selected_option_id: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    outcome: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    points_awarded: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    response_ms: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    hint_used: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    hint_removed_json: Mapped[dict | None] = mapped_column(
        MYSQL_JSON,
        nullable=True,
    )

    asked_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    context_json: Mapped[dict | None] = mapped_column(
        MYSQL_JSON,
        nullable=True,
    )

    # Participante al que pertenece el turno.
    game_player: Mapped["GamePlayer"] = relationship(
        "GamePlayer",
        back_populates="turns",
        foreign_keys="[GameTurn.game_id, GameTurn.game_player_id]",
    )

    # Pregunta que se presentó en este turno.
    question: Mapped["Question"] = relationship(
        "Question",
        foreign_keys=[question_id],
    )

    # Opción seleccionada. Es de solo lectura porque comparte
    # question_id con la relación question y la FK compuesta.
    selected_option: Mapped["QuestionOption | None"] = relationship(
        "QuestionOption",
        primaryjoin=(
            "and_("
            "GameTurn.question_id == QuestionOption.question_id, "
            "GameTurn.selected_option_id == QuestionOption.id"
            ")"
        ),
        foreign_keys="[GameTurn.question_id, GameTurn.selected_option_id]",
        viewonly=True,
        uselist=False,
    )

    # Preguntas sustituidas durante este turno.
    swaps: Mapped[list["TurnSwap"]] = relationship(
        "TurnSwap",
        back_populates="turn",
        order_by="TurnSwap.seq",
    )


class TurnSwap(Base):
    """Registro de preguntas sustituidas durante un turno."""

    __tablename__ = "turn_swaps"

    __table_args__ = (
        UniqueConstraint(
            "turn_id",
            "seq",
            name="uq_turn_swaps_turn_seq",
        ),
        CheckConstraint(
            "seq BETWEEN 1 AND 3",
            name="seq_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    turn_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "game_turns.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    seq: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    replaced_question_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    swapped_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Turno al que pertenece esta sustitución.
    turn: Mapped["GameTurn"] = relationship(
        "GameTurn",
        back_populates="swaps",
    )

    # Pregunta que fue sustituida.
    replaced_question: Mapped["Question"] = relationship(
        "Question",
        foreign_keys=[replaced_question_id],
    )
