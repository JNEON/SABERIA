# SABERIA --- Modelo de datos

> **Versión 1.1.** Diseño actualizado para MariaDB y MySQL. Define el
> modelo lógico y físico previo a la implementación ORM y las
> migraciones.
>
> **Motor de desarrollo:** MariaDB 10.4.32. **Compatibilidad prevista:**
> MariaDB 10.2.1 o superior y MySQL 8.0.16 o superior.
> **Almacenamiento:** InnoDB, `utf8mb4`. **Acceso:** SQLAlchemy 2,
> Alembic y PyMySQL.
>
> Ver también: [architecture.md](architecture.md) ·
> [question-package-format.md](question-package-format.md)

## 1. Objetivos y convenciones

El modelo permite administrar un banco superior a 100.000 preguntas,
clasificarlas por asignatura, tema y competencia, adaptar su selección a
la edad y dificultad de cada participante, registrar partidas y
conservar su historial. SABERIA funciona sin conexión a Internet.

-   Claves primarias `INT UNSIGNED AUTO_INCREMENT`; `BIGINT UNSIGNED`
    para `questions` y `game_turns`.
-   Estados y enumeraciones como `VARCHAR` con restricciones `CHECK`, no
    como `ENUM`.
-   `CHECK` se aplica desde MariaDB 10.2.1 y MySQL 8.0.16. La aplicación
    también valida las reglas.
-   Fechas UTC mediante `DATETIME(6)`.
-   No se almacena fecha de nacimiento ni edad exacta; solo la franja de
    edad.
-   Las relaciones históricas evitan borrar información que ya participa
    en una partida.
-   Las reglas que involucran varias filas o el flujo de una partida se
    validan en la aplicación.

## 2. Catálogos y valores permitidos

### 2.1 Franjas de edad

  Franja (`age_band`)     Edad mínima   Edad máxima
  --------------------- ------------- -------------
  `4-6`                             4             6
  `7-9`                             7             9
  `10-12`                          10            12
  `13-15`                          13            15
  `16-17`                          16            17
  `18+`                            18    Sin límite

En las preguntas, `age_max = NULL` representa que no existe límite
superior.

### 2.2 Tipos de pregunta

  Valor BD          Significado                                        Opciones
  ----------------- ------------------------------------------- ---------------
  `single_choice`   Selección de una única respuesta correcta             2 a 6
  `true_false`      Verdadero o falso                             Exactamente 2

El tipo Python `MULTIPLE_CHOICE` se persiste como `single_choice`,
porque el jugador selecciona una sola opción. `TRUE_FALSE` se persiste
como `true_false`.

### 2.3 Dificultad

La dificultad es independiente de la edad. Se utilizan cinco niveles
desde el inicio:

    Valor Nivel
  ------- ------------
        1 Muy básica
        2 Básica
        3 Intermedia
        4 Avanzada
        5 Experta

El dominio Python debe ofrecer los mismos cinco niveles y mapearlos
explícitamente a estos valores numéricos.

### 2.4 Otros valores

  -----------------------------------------------------------------------
  Campo                               Valores
  ----------------------------------- -----------------------------------
  `questions.origin`                  `own`, `open_source`, `ai_assisted`

  `questions.status`                  `draft`, `validated`, `published`,
                                      `retired`

  `games.mode`                        `roulette`, `board`

  `games.play_style`                  `competitive`, `cooperative`

  `games.status`                      `in_progress`, `finished`,
                                      `abandoned`

  `game_turns.outcome`                `correct`, `incorrect`, `skipped`,
                                      `timed_out`

  `game_players.timer_seconds`        10, 15, 20, 30, 45

  `game_players.difficulty`           1 a 5
  -----------------------------------------------------------------------

El MVP se concentra en `roulette` y `competitive`; `board` y
`cooperative` quedan reservados para ampliaciones.

## 3. Vista general de relaciones

La clasificación académica sigue la jerarquía **Asignatura → Tema →
Competencia → Pregunta**. Cada pregunta se vincula directamente con una
competencia; su asignatura y tema se obtienen mediante las relaciones
correspondientes. Esto evita guardar tres identificadores redundantes en
cada pregunta.

``` mermaid
erDiagram
    question_sources ||--o{ question_packages : "origina"
    question_packages ||--o{ questions : "contiene"
    categories ||--o{ topics : "agrupa"
    topics ||--o{ competencies : "desarrolla"
    competencies ||--o{ questions : "clasifica"
    questions ||--|{ question_options : "tiene"
    questions ||--o| questions : "reemplaza"
    games ||--|{ game_players : "incluye"
    players ||--o{ game_players : "participa"
    game_players ||--o{ game_turns : "juega"
    games ||--o{ game_turns : "contiene"
    questions ||--o{ game_turns : "se pregunta en"
    game_turns ||--o{ turn_swaps : "registra cambios"
    questions ||--o{ turn_swaps : "es descartada"
```

El diseño contempla **12 tablas**.

## 4. Catálogos de preguntas

### 4.1 `question_sources`

Registra la procedencia y condiciones de uso del contenido.

  --------------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- --------------------------
  `id`                    INT UNSIGNED            PK, AUTO_INCREMENT

  `name`                  VARCHAR(120)            NOT NULL

  `license_code`          VARCHAR(60)             NOT NULL. SPDX cuando
                                                  exista (`CC-BY-4.0`,
                                                  `CC0-1.0`, etc.) o
                                                  `LicenseRef-SABERIA-Own`
                                                  para contenido propio

  `license_url`           VARCHAR(255)            NULL

  `attribution_text`      VARCHAR(500)            NULL. Texto de atribución
                                                  exigido

  `url`                   VARCHAR(255)            NULL
  --------------------------------------------------------------------------

Una fuente puede tener varios paquetes. Las fuentes utilizadas por
paquetes existentes no se eliminan.

### 4.2 `question_packages`

Identifica paquetes de preguntas importados.

  -----------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- -----------------------
  `id`                    INT UNSIGNED            PK, AUTO_INCREMENT

  `package_uid`           CHAR(36)                NOT NULL. UUID

  `name`                  VARCHAR(120)            NOT NULL

  `version`               VARCHAR(20)             NOT NULL

  `source_id`             INT UNSIGNED            NOT NULL, FK →
                                                  `question_sources.id`

  `checksum_sha256`       CHAR(64)                NOT NULL. Huella para
                                                  importación idempotente

  `imported_at`           DATETIME(6)             NOT NULL, UTC
  -----------------------------------------------------------------------

Restricción: `UNIQUE (package_uid, version)`. El importador comprueba el
checksum antes de reprocesar un paquete. Las preguntas propias también
pertenecen a un paquete.

### 4.3 `categories`

Representa las asignaturas o áreas generales.

  Columna        Tipo                Restricciones y notas
  -------------- ------------------- -----------------------
  `id`           INT UNSIGNED        PK, AUTO_INCREMENT
  `code`         VARCHAR(40)         NOT NULL, UNIQUE
  `name`         VARCHAR(80)         NOT NULL
  `sort_order`   SMALLINT UNSIGNED   NOT NULL

Ejemplos: Matemáticas, Ciencias, Lengua Castellana, Inglés, Historia,
Geografía, Arte y Tecnología.

### 4.4 `topics`

Representa los temas de una asignatura.

  Columna         Tipo                Restricciones y notas
  --------------- ------------------- --------------------------------
  `id`            INT UNSIGNED        PK, AUTO_INCREMENT
  `category_id`   INT UNSIGNED        NOT NULL, FK → `categories.id`
  `code`          VARCHAR(60)         NOT NULL
  `name`          VARCHAR(100)        NOT NULL
  `description`   VARCHAR(255)        NULL
  `sort_order`    SMALLINT UNSIGNED   NOT NULL

Restricción: `UNIQUE (category_id, code)`. Ejemplos para Matemáticas:
aritmética, álgebra, geometría, estadística y probabilidad.

### 4.5 `competencies`

Representa las capacidades evaluadas dentro de un tema.

  Columna         Tipo           Restricciones y notas
  --------------- -------------- ----------------------------
  `id`            INT UNSIGNED   PK, AUTO_INCREMENT
  `topic_id`      INT UNSIGNED   NOT NULL, FK → `topics.id`
  `code`          VARCHAR(60)    NOT NULL
  `name`          VARCHAR(100)   NOT NULL
  `description`   VARCHAR(255)   NULL

Restricción: `UNIQUE (topic_id, code)`. Ejemplos: razonamiento lógico,
resolución de problemas, interpretación de información y comunicación
matemática.

## 5. Preguntas y opciones

### 5.1 `questions`

Cada pregunta se relaciona con una competencia; asignatura y tema se
obtienen mediante `competencies` y `topics`.

  -------------------------------------------------------------------------
  Columna                  Tipo                    Restricciones y notas
  ------------------------ ----------------------- ------------------------
  `id`                     BIGINT UNSIGNED         PK, AUTO_INCREMENT

  `package_id`             INT UNSIGNED            NOT NULL, FK →
                                                   `question_packages.id`

  `external_id`            VARCHAR(64)             NOT NULL. Identificador
                                                   dentro del paquete

  `replaces_question_id`   BIGINT UNSIGNED         NULL, FK →
                                                   `questions.id`

  `language`               VARCHAR(8)              NOT NULL. `es` en el MVP

  `competency_id`          INT UNSIGNED            NOT NULL, FK →
                                                   `competencies.id`

  `qtype`                  VARCHAR(16)             NOT NULL.
                                                   `single_choice` o
                                                   `true_false`

  `prompt`                 VARCHAR(500)            NOT NULL

  `explanation`            VARCHAR(1000)           NULL. Obligatoria para
                                                   publicar

  `media_path`             VARCHAR(255)            NULL. Ruta relativa
                                                   dentro de `assets/`

  `age_min`                TINYINT UNSIGNED        NOT NULL

  `age_max`                TINYINT UNSIGNED        NULL. NULL significa sin
                                                   límite superior

  `difficulty`             TINYINT UNSIGNED        NOT NULL. CHECK entre 1
                                                   y 5

  `origin`                 VARCHAR(16)             NOT NULL. Ver valores
                                                   permitidos

  `status`                 VARCHAR(16)             NOT NULL. Ver valores
                                                   permitidos

  `validated_by`           VARCHAR(80)             NULL

  `validated_at`           DATETIME(6)             NULL, UTC

  `content_hash`           CHAR(64)                NOT NULL. SHA-256 del
                                                   texto normalizado

  `created_at`             DATETIME(6)             NOT NULL, UTC

  `updated_at`             DATETIME(6)             NOT NULL, UTC
  -------------------------------------------------------------------------

Restricciones:

-   `UNIQUE (package_id, external_id)`.
-   `CHECK (age_min >= 4)`.
-   `CHECK (age_max IS NULL OR age_min <= age_max)`.
-   `CHECK (difficulty BETWEEN 1 AND 5)`.
-   `CHECK (qtype IN ('single_choice', 'true_false'))`.
-   `CHECK (origin IN ('own', 'open_source', 'ai_assisted'))`.
-   `CHECK (status IN ('draft', 'validated', 'published', 'retired'))`.
-   Si `origin = 'ai_assisted'` y `status = 'published'`, deben existir
    `validated_by` y `validated_at`.

Para publicar, `explanation` debe estar diligenciada; esta regla también
se valida en el servicio de publicación.

Índices:

-   `UNIQUE (package_id, external_id)`.
-   `(status, language, competency_id, difficulty, age_min, age_max)`
    para selección.
-   `(content_hash)` para duplicados.
-   `(competency_id)` para analítica.

**Inmutabilidad:** una pregunta publicada no se edita. Para corregirla
se crea una versión nueva con `replaces_question_id`; la anterior pasa a
`retired`. Así, el historial conserva el contenido utilizado.

### 5.2 `question_options`

Almacena las opciones de respuesta.

  -----------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- -----------------------
  `id`                    INT UNSIGNED            PK, AUTO_INCREMENT

  `question_id`           BIGINT UNSIGNED         NOT NULL, FK →
                                                  `questions.id` ON
                                                  DELETE CASCADE

  `position`              TINYINT UNSIGNED        NOT NULL

  `text`                  VARCHAR(255)            NOT NULL

  `is_correct`            BOOLEAN                 NOT NULL
  -----------------------------------------------------------------------

Restricciones: `UNIQUE (question_id, position)` y
`UNIQUE (question_id, id)`. La segunda permite garantizar mediante FK
compuesta que la opción seleccionada pertenece a la pregunta del turno.

El dominio y el importador validan:

-   `single_choice`: entre 2 y 6 opciones y exactamente una correcta.
-   `true_false`: exactamente 2 opciones y exactamente una correcta.

La base de datos no garantiza por sí sola que exista exactamente una
opción correcta por pregunta; esa regla corresponde al validador y al
servicio de publicación.

## 6. Jugadores y partidas

### 6.1 `players`

  Columna          Tipo           Restricciones y notas
  ---------------- -------------- -----------------------
  `id`             INT UNSIGNED   PK, AUTO_INCREMENT
  `display_name`   VARCHAR(60)    NOT NULL
  `age_band`       VARCHAR(5)     NOT NULL
  `avatar_key`     VARCHAR(40)    NULL
  `created_at`     DATETIME(6)    NOT NULL, UTC
  `archived_at`    DATETIME(6)    NULL, UTC

No se guarda fecha de nacimiento ni edad exacta. Los perfiles se
archivan en lugar de eliminarse cuando tienen historial.

### 6.2 `games`

  -----------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- -----------------------
  `id`                    INT UNSIGNED            PK, AUTO_INCREMENT

  `mode`                  VARCHAR(16)             NOT NULL. `roulette` o
                                                  `board`

  `play_style`            VARCHAR(16)             NOT NULL. `competitive`
                                                  o `cooperative`

  `language`              VARCHAR(8)              NOT NULL

  `rng_seed`              BIGINT                  NOT NULL.
                                                  Reproducibilidad de
                                                  sorteos y selección

  `config_json`           JSON                    NOT NULL. Configuración
                                                  general

  `status`                VARCHAR(16)             NOT NULL

  `started_at`            DATETIME(6)             NOT NULL, UTC

  `ended_at`              DATETIME(6)             NULL, UTC
  -----------------------------------------------------------------------

`config_json` puede contener `rounds`, `hint_per_turn` (0 o 1; por
defecto 0) y `swaps_per_turn` (máximo 3). La aplicación valida su
estructura y valores.

En MariaDB 10.4, `JSON` es un alias basado en `LONGTEXT`, no el
almacenamiento binario interno de MySQL. No se dependerá de
características exclusivas del JSON binario de MySQL.

### 6.3 `game_players`

  -----------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- -----------------------
  `id`                    INT UNSIGNED            PK, AUTO_INCREMENT

  `game_id`               INT UNSIGNED            NOT NULL, FK →
                                                  `games.id`

  `player_id`             INT UNSIGNED            NOT NULL, FK →
                                                  `players.id`

  `seat`                  TINYINT UNSIGNED        NOT NULL. Orden de
                                                  turno, entre 1 y 8

  `age_band`              VARCHAR(5)              NOT NULL. Copia de la
                                                  franja usada en la
                                                  partida

  `difficulty`            TINYINT UNSIGNED        NOT NULL. Entre 1 y 5

  `timer_seconds`         TINYINT UNSIGNED        NOT NULL. 10, 15, 20,
                                                  30 o 45

  `final_score`           INT UNSIGNED            NULL
  -----------------------------------------------------------------------

Restricciones:

-   `UNIQUE (game_id, seat)`.
-   `UNIQUE (game_id, player_id)`.
-   `UNIQUE (game_id, id)` para validar la pertenencia del participante
    a la partida desde `game_turns`.
-   `CHECK (seat BETWEEN 1 AND 8)`.
-   `CHECK (difficulty BETWEEN 1 AND 5)`.
-   `CHECK (timer_seconds IN (10, 15, 20, 30, 45))`.

La edad y dificultad se guardan por jugador y por partida. El MVP admite
de 2 a 4 participantes; el modelo permite de 2 a 8. La cantidad mínima y
máxima se valida al crear la partida.

### 6.4 `game_turns`

  -----------------------------------------------------------------------
  Columna                 Tipo                    Restricciones y notas
  ----------------------- ----------------------- -----------------------
  `id`                    BIGINT UNSIGNED         PK, AUTO_INCREMENT

  `game_id`               INT UNSIGNED            NOT NULL, FK →
                                                  `games.id`

  `game_player_id`        INT UNSIGNED            NOT NULL. Participante
                                                  que responde

  `turn_no`               SMALLINT UNSIGNED       NOT NULL. Consecutivo
                                                  global de la partida

  `question_id`           BIGINT UNSIGNED         NOT NULL, FK →
                                                  `questions.id`.
                                                  Pregunta final del
                                                  turno

  `selected_option_id`    INT UNSIGNED            NULL si se omitió o
                                                  venció el tiempo

  `outcome`               VARCHAR(16)             NOT NULL

  `points_awarded`        TINYINT UNSIGNED        NOT NULL. 0 o 1

  `response_ms`           INT UNSIGNED            NULL. Tiempo real en
                                                  milisegundos

  `hint_used`             BOOLEAN                 NOT NULL

  `hint_removed_json`     JSON                    NULL. Identificadores
                                                  de opciones eliminadas

  `asked_at`              DATETIME(6)             NOT NULL, UTC

  `context_json`          JSON                    NULL. Segmento de
                                                  ruleta o casilla del
                                                  tablero
  -----------------------------------------------------------------------

Restricciones e índices:

-   `UNIQUE (game_id, turn_no)`.
-   FK compuesta `(game_id, game_player_id)` →
    `game_players(game_id, id)`, para garantizar que el participante
    pertenece a la partida.
-   FK compuesta `(question_id, selected_option_id)` →
    `question_options(question_id, id)`, para garantizar que la opción
    pertenece a la pregunta. `selected_option_id` puede ser NULL.
-   `CHECK (outcome IN ('correct', 'incorrect', 'skipped', 'timed_out'))`.
-   `CHECK (points_awarded IN (0, 1))`.
-   Índices `(game_player_id, outcome)` y `(question_id)`.

`turn_no` es consecutivo global de la partida, no un contador
independiente por jugador. El dominio Python usa `TIMEOUT`; la capa de
persistencia lo convierte a `timed_out`.

## 7. Cambios de pregunta: `turn_swaps`

Registra las preguntas descartadas durante un turno.
`game_turns.question_id` conserva únicamente la pregunta final.

  ------------------------------------------------------------------------
  Columna                  Tipo                    Restricciones y notas
  ------------------------ ----------------------- -----------------------
  `id`                     INT UNSIGNED            PK, AUTO_INCREMENT

  `turn_id`                BIGINT UNSIGNED         NOT NULL, FK →
                                                   `game_turns.id`

  `seq`                    TINYINT UNSIGNED        NOT NULL. Secuencia
                                                   entre 1 y 3

  `replaced_question_id`   BIGINT UNSIGNED         NOT NULL, FK →
                                                   `questions.id`

  `swapped_at`             DATETIME(6)             NOT NULL, UTC
  ------------------------------------------------------------------------

Restricciones: `UNIQUE (turn_id, seq)` y `CHECK (seq BETWEEN 1 AND 3)`.
La aplicación garantiza que no se repitan preguntas en la partida y que
la pregunta descartada no sea la pregunta final del turno.

## 8. Reglas de juego que deben respetarse

Se implementan en el motor de juego y se prueban independientemente de
la interfaz:

-   Correcta: 1 punto y termina el turno.
-   Incorrecta: 0 puntos y termina el turno.
-   Tiempo agotado: 0 puntos y termina el turno.
-   Pasar: 0 puntos y registra `skipped`.
-   Cambiar pregunta: consume un cambio, no modifica la puntuación y
    reinicia el temporizador.
-   Máximo 3 cambios por participante y turno.
-   La pista es opcional, está desactivada por defecto y se usa una vez
    por turno.
-   La pista elimina dos opciones incorrectas solo en preguntas
    `single_choice` con 4 o más opciones. No aplica a verdadero/falso.
-   Cambiar pregunta después de usar la pista no restablece su uso.
-   Las respuestas con pista no se utilizan para evaluar el nivel de
    competencia.
-   Correctas, incorrectas, omitidas y tiempos agotados se registran por
    separado.
-   No se repiten preguntas dentro de una partida, incluidas las
    descartadas.

La persistencia registra los datos necesarios; el motor hace cumplir las
reglas durante la ejecución.

## 9. Consultas clave

### 9.1 Perfil acumulado por competencia

Las omitidas, los tiempos agotados y las respuestas con pista no son
evaluables. El mínimo de cinco respuestas evaluables y los niveles de
desempeño se calculan en `analytics/`, no en SQL.

``` sql
SELECT
    q.competency_id,
    SUM(t.outcome = 'correct') AS aciertos,
    COUNT(*) AS evaluables
FROM game_turns t
JOIN game_players gp ON gp.id = t.game_player_id
JOIN questions q ON q.id = t.question_id
WHERE gp.player_id = :player_id
  AND t.outcome IN ('correct', 'incorrect')
  AND t.hint_used = 0
GROUP BY q.competency_id;
```

La asignatura y el tema se obtienen mediante `competencies` → `topics` →
`categories`.

### 9.2 Selección de preguntas candidatas

La edad es una restricción dura. La dificultad solicitada prioriza
candidatas; el motor puede ampliar a niveles cercanos si faltan
preguntas, pero nunca relaja la edad.

``` sql
SELECT q.id
FROM questions q
JOIN competencies comp ON comp.id = q.competency_id
JOIN topics tp ON tp.id = comp.topic_id
JOIN categories cat ON cat.id = tp.category_id
WHERE q.status = 'published'
  AND q.language = :lang
  AND cat.id = :category_id
  AND q.difficulty = :difficulty
  AND q.age_min <= :band_max
  AND (q.age_max IS NULL OR q.age_max >= :band_min)
  AND NOT EXISTS (
      SELECT 1
      FROM game_turns t
      WHERE t.game_id = :game_id
        AND t.question_id = q.id
  )
  AND NOT EXISTS (
      SELECT 1
      FROM turn_swaps ts
      JOIN game_turns t2 ON t2.id = ts.turn_id
      WHERE t2.game_id = :game_id
        AND ts.replaced_question_id = q.id
  );
```

Para `18+`, `:band_max` se interpreta como límite superior abierto; la
implementación de la consulta debe adaptar esa condición. El muestreo se
realiza sobre las candidatas filtradas, nunca mediante `ORDER BY RAND()`
sobre toda la tabla.

## 10. Compatibilidad MariaDB

-   Todas las tablas usan InnoDB y `utf8mb4`.
-   Las claves foráneas deben utilizar tipos compatibles, incluido
    `UNSIGNED` cuando corresponda.
-   MariaDB 10.4 admite las restricciones `CHECK` utilizadas.
-   SQLAlchemy puede utilizar su tipo JSON; en MariaDB 10.4 se almacena
    como texto largo con validación JSON. La aplicación valida
    estructura y contenido.
-   Las migraciones Alembic deben probarse contra la instancia real
    MariaDB 10.4.32.
-   MySQL 8.0.16 o superior sigue siendo una alternativa prevista; no es
    necesario instalarlo para el desarrollo actual.

## 11. Escalabilidad: más de 100.000 preguntas

-   `BIGINT` en `questions` y `game_turns`.
-   Índice compuesto para selección.
-   `content_hash` para detectar duplicados.
-   Contadores de uso y preguntas vistas derivados de `game_turns` y
    `turn_swaps`.
-   No se crean cachés hasta que las mediciones demuestren que son
    necesarias.
-   Los paquetes grandes se importan por lotes (ver
    [question-package-format.md](question-package-format.md)).
-   La selección trabaja sobre candidatas filtradas por estado, idioma,
    competencia, dificultad y edad.

## 12. Fuera del MVP

-   `team_no` en `game_players` para equipos del modo cooperativo.
-   Persistencia detallada del tablero; inicialmente se describe en
    JSON.
-   Sincronización en red, cuentas en la nube y API remota.
-   Banco masivo: el esquema lo soporta, pero el MVP comienza con un
    conjunto reducido y validado.

## 13. Verificaciones antes de la primera migración

1.  Actualizar los enums Python para representar los cinco niveles de
    dificultad.
2.  Mapear `MULTIPLE_CHOICE` → `single_choice` y `TRUE_FALSE` →
    `true_false`.
3.  Resolver categoría, tema y competencia del dominio mediante la
    jerarquía normalizada.
4.  Mapear `AnswerStatus.TIMEOUT` → `timed_out`.
5.  Probar las FK compuestas de `game_turns` en MariaDB 10.4.32.
6.  Verificar columnas JSON y restricciones CHECK en la base real.
7.  Ejecutar las migraciones exclusivamente sobre `saberiadb` durante el
    desarrollo.
