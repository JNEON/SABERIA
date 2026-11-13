"""Pruebas de persistencia real contra MariaDB.

Se ejecutan únicamente cuando SABERIA_TEST_MARIADB=1.
Todas las operaciones se realizan dentro de una transacción externa
que se revierte al terminar cada prueba.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from saberia.config.settings import load_settings
from saberia.persistence.database import (
    create_engine_from_settings,
    session_scope,
)
from saberia.persistence.models import (
    Category,
    Competency,
    Game,
    GamePlayer,
    GameTurn,
    Player,
    Question,
    QuestionOption,
    QuestionPackage,
    QuestionSource,
    Topic,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("SABERIA_TEST_MARIADB") != "1",
    reason="Activa SABERIA_TEST_MARIADB=1 para ejecutar las pruebas reales.",
)


@pytest.fixture
def session_factory():
    """Proporciona sesiones aisladas mediante una transacción externa."""
    settings = load_settings()

    # Protección: nunca permitir que estas pruebas apunten a otra BD.
    if settings.db_name != "saberiadb":
        pytest.fail("Prueba cancelada: la base de datos debe ser exactamente 'saberiadb'.")

    engine = create_engine_from_settings(settings)
    connection = engine.connect()
    outer_transaction = connection.begin()

    factory = sessionmaker(
        bind=connection,
        autoflush=True,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield factory
    finally:
        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()
        engine.dispose()


def test_persistencia_de_taxonomia_pregunta_y_partida(session_factory):
    """Comprueba la persistencia de un recorrido completo de datos."""
    suffix = uuid4().hex[:12]

    with session_scope(session_factory) as session:
        # 1. Taxonomía académica.
        category = Category(
            code=f"IT-{suffix}",
            name="Categoría de integración",
            sort_order=1,
        )

        topic = Topic(
            category=category,
            code=f"T-{suffix}",
            name="Tema de integración",
        )

        competency = Competency(
            topic=topic,
            code=f"C-{suffix}",
            name="Competencia de integración",
        )

        # 2. Procedencia y paquete de preguntas.
        source = QuestionSource(
            name="Fuente de prueba de integración",
            license_code="OWN",
        )

        package = QuestionPackage(
            package_uid=str(uuid4()),
            name="Paquete de integración",
            version="1.0.0",
            source=source,
            checksum_sha256="b" * 64,
        )

        # 3. Pregunta y opciones.
        question = Question(
            package=package,
            external_id=f"Q-{suffix}",
            language="es",
            competency=competency,
            qtype="single_choice",
            prompt="¿Cuál es el resultado de 2 + 2?",
            explanation="La suma de dos y dos es cuatro.",
            age_min=7,
            age_max=9,
            difficulty=1,
            origin="own",
            status="draft",
            content_hash="a" * 64,
        )

        correct_option = QuestionOption(
            question=question,
            position=1,
            text="4",
            is_correct=True,
        )

        QuestionOption(
            question=question,
            position=2,
            text="5",
            is_correct=False,
        )

        # 4. Jugador y partida.
        player = Player(
            display_name=f"Jugador IT {suffix}",
            age_band="7-9",
        )

        game = Game(
            rng_seed=12345,
            config_json={"integration_test": True},
        )

        session.add_all([category, source, player, game])
        session.flush()

        game_player = GamePlayer(
            game=game,
            player=player,
            seat=1,
            age_band="7-9",
            difficulty=1,
            timer_seconds=15,
        )

        session.add(game_player)
        session.flush()

        # 5. Turno con opción seleccionada.
        turn = GameTurn(
            game_player=game_player,
            question=question,
            turn_no=1,
            selected_option_id=correct_option.id,
            outcome="correct",
            points_awarded=1,
            response_ms=2500,
            hint_used=False,
        )

        session.add(turn)
        session.flush()

        # Verificar relaciones y datos persistidos.
        stored_category = session.scalar(select(Category).where(Category.code == f"IT-{suffix}"))

        assert stored_category is not None
        assert stored_category.topics[0].competencies[0].questions[0].prompt == (
            "¿Cuál es el resultado de 2 + 2?"
        )

        assert len(question.options) == 2
        assert turn.game_player.player.display_name == f"Jugador IT {suffix}"
        assert turn.selected_option is not None
        assert turn.selected_option.is_correct is True


def test_restriccion_check_de_age_band(session_factory):
    """Comprueba que MariaDB aplique una restricción CHECK del modelo."""
    with pytest.raises(OperationalError) as exc_info:
        with session_scope(session_factory) as session:
            session.add(
                Player(
                    display_name="Jugador inválido",
                    age_band="99",
                )
            )
            session.flush()

    # MariaDB utiliza el código 4025 para violaciones de CHECK.
    assert exc_info.value.orig.args[0] == 4025


def test_reversion_automatica_ante_excepcion(session_factory):
    """Comprueba que session_scope revierta los cambios ante una excepción."""
    suffix = uuid4().hex[:12]
    category_code = f"ROLLBACK-{suffix}"

    with pytest.raises(RuntimeError, match="Error intencional"):
        with session_scope(session_factory) as session:
            session.add(
                Category(
                    code=category_code,
                    name="Categoría temporal",
                )
            )
            session.flush()
            raise RuntimeError("Error intencional")

    with session_scope(session_factory) as session:
        stored_category = session.scalar(select(Category).where(Category.code == category_code))

        assert stored_category is None
