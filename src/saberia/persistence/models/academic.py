"""Modelos de la taxonomía académica de SABERIA."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saberia.persistence.base import Base

if TYPE_CHECKING:
    from saberia.persistence.models.questions import Question


class Category(Base):
    """Asignatura o categoría académica."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        SMALLINT(unsigned=True),
        nullable=False,
        default=0,
    )

    # Temas pertenecientes a esta asignatura.
    topics: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="category",
    )


class Topic(Base):
    """Tema perteneciente a una asignatura."""

    __tablename__ = "topics"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "code",
            name="uq_topics_category_code",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    category_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        SMALLINT(unsigned=True),
        nullable=False,
        default=0,
    )

    # Asignatura a la que pertenece este tema.
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="topics",
    )

    # Competencias asociadas al tema.
    competencies: Mapped[list["Competency"]] = relationship(
        "Competency",
        back_populates="topic",
    )


class Competency(Base):
    """Competencia asociada a un tema académico."""

    __tablename__ = "competencies"

    __table_args__ = (
        UniqueConstraint(
            "topic_id",
            "code",
            name="uq_competencies_topic_code",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    topic_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "topics.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Tema al que pertenece esta competencia.
    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="competencies",
    )

    # Preguntas clasificadas dentro de esta competencia.
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="competency",
    )
