"""Entidades principales del dominio de SABERIA."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from saberia.domain.enums import AgeGroup, AnswerStatus, Difficulty, QuestionType


@dataclass(frozen=True)
class Player:
    """Representa a un participante del juego."""

    player_id: str
    name: str
    age: int

    def __post_init__(self) -> None:
        if not self.player_id.strip():
            raise ValueError("El identificador del participante es obligatorio.")

        if not self.name.strip():
            raise ValueError("El nombre del participante es obligatorio.")

        AgeGroup.from_age(self.age)

    @property
    def age_group(self) -> AgeGroup:
        """Devuelve el grupo de edad del participante."""
        return AgeGroup.from_age(self.age)


@dataclass(frozen=True)
class QuestionOption:
    """Representa una opción de respuesta de una pregunta."""

    option_id: str
    text: str

    def __post_init__(self) -> None:
        if not self.option_id.strip():
            raise ValueError("El identificador de la opción es obligatorio.")

        if not self.text.strip():
            raise ValueError("El texto de la opción es obligatorio.")


@dataclass(frozen=True)
class Question:
    """Representa una pregunta del banco educativo."""

    question_id: str
    statement: str
    competency_id: str
    age_min: int
    age_max: int | None
    difficulty: Difficulty
    question_type: QuestionType
    options: tuple[QuestionOption, ...]
    correct_option_id: str
    explanation: str = ""
    source: str = ""
    language: str = "es"

    def __post_init__(self) -> None:
        if not self.question_id.strip():
            raise ValueError("El identificador de la pregunta es obligatorio.")

        if not self.statement.strip():
            raise ValueError("El enunciado de la pregunta es obligatorio.")

        if not self.competency_id.strip():
            raise ValueError("La competencia es obligatoria.")

        if self.age_min < 4:
            raise ValueError("La edad mínima de una pregunta debe ser 4 años o más.")

        if self.age_max is not None and self.age_max < self.age_min:
            raise ValueError("La edad máxima no puede ser menor que la mínima.")

        if not isinstance(self.difficulty, Difficulty):
            raise ValueError("La dificultad de la pregunta no es válida.")

        if not isinstance(self.question_type, QuestionType):
            raise ValueError("El tipo de pregunta no es válido.")

        if not self.options:
            raise ValueError("La pregunta debe tener opciones de respuesta.")

        option_ids = [option.option_id for option in self.options]

        if len(option_ids) != len(set(option_ids)):
            raise ValueError("La pregunta no puede tener opciones duplicadas.")

        if self.correct_option_id not in option_ids:
            raise ValueError("La respuesta correcta debe existir entre las opciones.")

        if self.question_type == QuestionType.TRUE_FALSE and len(self.options) != 2:
            raise ValueError("Las preguntas verdadero/falso deben tener dos opciones.")

        if self.question_type == QuestionType.SINGLE_CHOICE and len(self.options) < 2:
            raise ValueError("La selección múltiple requiere al menos dos opciones.")

    def is_allowed_for_age(self, age: int) -> bool:
        """Indica si la pregunta está permitida para una edad determinada."""
        if isinstance(age, bool) or not isinstance(age, int) or age < 4:
            return False

        return age >= self.age_min and (self.age_max is None or age <= self.age_max)


@dataclass(frozen=True)
class AnswerRecord:
    """Registra el resultado de un participante ante una pregunta."""

    player_id: str
    question_id: str
    status: AnswerStatus
    selected_option_id: str | None
    elapsed_seconds: float
    used_hint: bool = False
    answered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.player_id.strip():
            raise ValueError("El participante es obligatorio.")

        if not self.question_id.strip():
            raise ValueError("La pregunta es obligatoria.")

        if not isinstance(self.status, AnswerStatus):
            raise ValueError("El estado de la respuesta no es válido.")

        if self.elapsed_seconds < 0:
            raise ValueError("El tiempo de respuesta no puede ser negativo.")

        if self.status in (AnswerStatus.CORRECT, AnswerStatus.INCORRECT):
            if not self.selected_option_id:
                raise ValueError("Debe registrarse la opción seleccionada.")

        if self.status in (AnswerStatus.SKIPPED, AnswerStatus.TIMEOUT):
            if self.selected_option_id is not None:
                raise ValueError(
                    "Las preguntas omitidas o agotadas no deben tener opción seleccionada."
                )


@dataclass
class GameSession:
    """Representa una partida y controla las preguntas utilizadas."""

    session_id: str
    player_ids: tuple[str, ...]
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    asked_question_ids: set[str] = field(default_factory=set)
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("El identificador de la partida es obligatorio.")

        if not 2 <= len(self.player_ids) <= 8:
            raise ValueError("Una partida debe tener entre 2 y 8 participantes.")

        if len(self.player_ids) != len(set(self.player_ids)):
            raise ValueError("No puede haber participantes duplicados.")

        if any(not player_id.strip() for player_id in self.player_ids):
            raise ValueError("Todos los participantes deben tener identificador.")

    def register_question(self, question_id: str) -> None:
        """Registra una pregunta e impide que se repita en la partida."""
        if not question_id.strip():
            raise ValueError("El identificador de la pregunta es obligatorio.")

        if question_id in self.asked_question_ids:
            raise ValueError("Esta pregunta ya fue utilizada en la partida.")

        self.asked_question_ids.add(question_id)

    @property
    def is_finished(self) -> bool:
        """Indica si la partida ha finalizado."""
        return self.finished_at is not None
