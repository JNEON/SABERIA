"""Modelos del catálogo y procedencia de preguntas."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import (
    BIGINT,
    CHAR,
    DATETIME,
    INTEGER,
    TINYINT,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saberia.persistence.base import Base
from saberia.persistence.models.academic import Competency


class QuestionSource(Base):
    """Fuente de origen de una colección de preguntas."""

    __tablename__ = "question_sources"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    license_code: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )

    license_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    attribution_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    packages: Mapped[list["QuestionPackage"]] = relationship(
        "QuestionPackage",
        back_populates="source",
    )


class QuestionPackage(Base):
    """Paquete o colección versionada de preguntas."""

    __tablename__ = "question_packages"

    __table_args__ = (
        UniqueConstraint(
            "package_uid",
            "version",
            name="uq_question_packages_uid_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    package_uid: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    source_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "question_sources.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    checksum_sha256: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
    )

    imported_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    source: Mapped["QuestionSource"] = relationship(
        "QuestionSource",
        back_populates="packages",
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="package",
        passive_deletes=True,
    )


class Question(Base):
    """Pregunta del banco central de SABERIA."""

    __tablename__ = "questions"

    __table_args__ = (
        UniqueConstraint(
            "package_id",
            "external_id",
            name="uq_questions_package_external",
        ),
        CheckConstraint(
            "age_min >= 4",
            name="age_min_valid",
        ),
        CheckConstraint(
            "age_max IS NULL OR age_max >= age_min",
            name="age_max_valid",
        ),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5",
            name="difficulty_valid",
        ),
        CheckConstraint(
            "qtype IN ('single_choice', 'true_false')",
            name="qtype_valid",
        ),
        CheckConstraint(
            "origin IN ('own', 'open_source', 'ai_assisted')",
            name="origin_valid",
        ),
        CheckConstraint(
            "status IN ('draft', 'validated', 'published', 'retired')",
            name="status_valid",
        ),
        CheckConstraint(
            "status != 'published' OR explanation IS NOT NULL",
            name="published_requires_explanation",
        ),
        CheckConstraint(
            """
            origin != 'ai_assisted'
            OR status != 'published'
            OR (
                validated_by IS NOT NULL
                AND validated_at IS NOT NULL
            )
            """,
            name="ai_published_requires_validation",
        ),
        Index("ix_questions_status", "status"),
        Index("ix_questions_language", "language"),
        Index("ix_questions_competency_id", "competency_id"),
        Index("ix_questions_difficulty", "difficulty"),
        Index("ix_questions_age_min", "age_min"),
        Index("ix_questions_age_max", "age_max"),
        Index("ix_questions_content_hash", "content_hash"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    package_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "question_packages.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    replaces_question_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )

    competency_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey(
            "competencies.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    qtype: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    prompt: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    media_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    age_min: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    age_max: Mapped[int | None] = mapped_column(
        TINYINT(unsigned=True),
        nullable=True,
    )

    difficulty: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    origin: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="draft",
    )

    validated_by: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DATETIME(fsp=6),
        nullable=True,
    )

    content_hash: Mapped[str] = mapped_column(
        CHAR(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    package: Mapped["QuestionPackage"] = relationship(
        "QuestionPackage",
        back_populates="questions",
    )

    competency: Mapped["Competency"] = relationship(
        "Competency",
        back_populates="questions",
    )

    replaces_question: Mapped["Question | None"] = relationship(
        "Question",
        remote_side="Question.id",
        back_populates="replacement_questions",
    )

    replacement_questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="replaces_question",
    )

    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        passive_deletes=True,
    )


class QuestionOption(Base):
    """Opción de respuesta asociada a una pregunta."""

    __tablename__ = "question_options"

    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "position",
            name="uq_question_options_question_position",
        ),
        UniqueConstraint(
            "question_id",
            "id",
            name="uq_question_options_question_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    question_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options",
    )
