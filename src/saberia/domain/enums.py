"""Enumeraciones fundamentales del dominio de SABERIA."""

from enum import Enum


class AgeGroup(Enum):
    """Rangos de edad admitidos para los participantes."""

    AGE_4_6 = ("4-6", 4, 6)
    AGE_7_9 = ("7-9", 7, 9)
    AGE_10_12 = ("10-12", 10, 12)
    AGE_13_15 = ("13-15", 13, 15)
    AGE_16_17 = ("16-17", 16, 17)
    AGE_18_PLUS = ("18+", 18, None)

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def min_age(self) -> int:
        return self.value[1]

    @property
    def max_age(self) -> int | None:
        return self.value[2]

    @classmethod
    def from_age(cls, age: int) -> "AgeGroup":
        """Obtiene el rango correspondiente a una edad."""
        if isinstance(age, bool) or not isinstance(age, int):
            raise ValueError("La edad debe ser un número entero.")

        for group in cls:
            if age >= group.min_age and (group.max_age is None or age <= group.max_age):
                return group

        raise ValueError("La edad debe ser igual o superior a 4 años.")


class Difficulty(Enum):
    """Dificultad de las preguntas, independiente de la edad."""

    VERY_BASIC = 1
    BASIC = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

    @property
    def label(self) -> str:
        """Nombre del nivel de dificultad en español."""
        labels = {
            Difficulty.VERY_BASIC: "Muy básica",
            Difficulty.BASIC: "Básica",
            Difficulty.INTERMEDIATE: "Intermedia",
            Difficulty.ADVANCED: "Avanzada",
            Difficulty.EXPERT: "Experta",
        }
        return labels[self]


class QuestionType(Enum):
    """Modalidades de preguntas admitidas."""

    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE = "true_false"


class AnswerStatus(Enum):
    """Resultado de la participación ante una pregunta."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
