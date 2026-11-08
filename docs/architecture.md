# SABERIA — Arquitectura

> **Versión 1.** Diseño aprobado. Estado de implementación: andamiaje inicial (configuración,
> prueba de conexión con MySQL y ventana mínima de Flet). El motor de juego, la ruleta y las
> pantallas funcionales **no están implementados todavía**.
>
> Documentos relacionados: [data-model.md](data-model.md) ·
> [question-package-format.md](question-package-format.md)

## 1. Contexto y objetivos

SABERIA es un videojuego educativo familiar de preguntas y aprendizaje. Se desarrolla en
**escritorio primero**, con una arquitectura que permita evolucionar a web y a dispositivos móviles.

### 1.1 Familia de prueba (MVP)

Las primeras pruebas se harán con **un niño de 9 años y dos adultos mayores de 30**.

- Franjas de edad en juego: **7-9** (niño) y **18+** (adultos).
- Objetivo educativo para el niño: **mejorar en matemáticas** y reforzar los conocimientos en
  el resto de áreas.
- Consecuencias de diseño:
  - La edad orienta el contenido y la dificultad se configura **por jugador y de forma
    independiente** (el niño puede jugar la dificultad que le convenga dentro de su franja).
  - El banco inicial se concentra en 7-9 y 18+ y da **más peso a Matemáticas** (sección 8).
  - El perfil acumulado por competencia es la herramienta principal de seguimiento del niño
    (sección 7).

## 2. Decisiones cerradas

| # | Tema | Decisión |
|---|---|---|
| 1 | Plataforma | Escritorio primero; arquitectura preparada para web y móvil |
| 2 | Público | Desde 4 años hasta adultos; la edad orienta el contenido, la dificultad es independiente |
| 3 | Participantes | De 2 a 8; el MVP se prueba con 2 a 4 |
| 4 | Modalidades | Ruleta y tablero sobre el mismo motor y las mismas reglas. **Ruleta primero**; tablero en la fase 2 |
| 5 | Estilo | Competitivo primero; cooperativo después |
| 6 | Preguntas | Banco híbrido (propias, fuentes abiertas con licencia compatible, asistidas por IA con validación). El banco inicial del MVP es **solo de preguntas propias** |
| 7 | Almacenamiento | MySQL 8 local (SQLAlchemy, Alembic, PyMySQL). JSON solo para importar/exportar paquetes |
| 8 | Conectividad | Funciona sin internet mientras el servidor MySQL local esté disponible |
| 9 | Resultados | Puntuación, aciertos, errores, omitidas, tiempo de respuesta, fortalezas y competencias por reforzar |
| 10 | Crecimiento | Modelo de datos preparado para más de 100.000 preguntas, sin cargarlo ni desarrollarlo en el MVP |

## 3. Principios

- **Python + Flet** para la interfaz. El motor de juego no conoce Flet.
- **Motor independiente** del modo (ruleta/tablero) y del estilo (competitivo/cooperativo).
- **SQL portable**: sin `ENUM` de MySQL ni funciones propias, para poder cambiar de motor si la
  distribución final lo exige.
- **Todo el contenido entra por paquetes JSON**, también las preguntas propias.
- **Regla de dependencias:** `ui → engine / analytics / packages → domain ← persistence`.
  El dominio no importa nada del resto; el motor solo conoce la base de datos mediante puertos.

## 4. Estructura de carpetas

`(creado)` = existe en el andamiaje inicial; `(pendiente)` = diseñado, aún sin implementar.

```
SABERIA/
├── pyproject.toml              (creado) dependencias y versiones acotadas
├── .env.example                (creado) plantilla de configuración; el .env real está ignorado
├── README.md                   (creado) instalación, configuración y ejecución
├── alembic.ini                 (pendiente)
├── migrations/                 (creado, vacío) migraciones de Alembic
├── docs/                       (creado) architecture.md, data-model.md, question-package-format.md
├── content/                    (creado, vacío)
│   ├── schema/                 (pendiente) JSON Schema del paquete de preguntas
│   └── packages/               (pendiente) paquetes versionados (banco inicial)
├── src/saberia/
│   ├── main.py, __main__.py    (creado) punto de entrada
│   ├── config/                 (creado) settings.py: carga y validación de configuración
│   ├── persistence/
│   │   ├── database.py         (creado) conexión de prueba con MySQL
│   │   ├── models.py           (pendiente) ORM
│   │   └── repositories/       (creado, vacío)
│   ├── ui/
│   │   ├── app.py              (creado) ventana mínima de diagnóstico
│   │   ├── views/              (creado, vacío)
│   │   └── components/         (creado, vacío)
│   ├── domain/                 (creado, vacío) entidades, enums y puertos
│   ├── engine/                 (creado, vacío)
│   │   ├── rules/              competitive.py; cooperative.py llegará después
│   │   └── modes/              roulette.py; board.py en la fase 2
│   │   (pendientes: session, selector, scoring, helps, clock)
│   ├── analytics/              (creado, vacío)
│   ├── packages/               (creado, vacío) validador, importador, exportador
│   └── assets/                 (creado) fuentes e imágenes locales
├── tools/                      (creado, vacío) scripts auxiliares
└── tests/                      (creado) pruebas automatizadas
```

> **Nombres de carpeta prohibidos.** El `.gitignore` (plantilla de Python) ignora cualquier carpeta
> llamada `build`, `lib`, `lib64`, `downloads`, `parts`, `var`, `eggs`, `sdist`, `wheels`, `dist`,
> `target` o `cover`, y archivos `*.mo`, `*.pot`, `*.log`, `*.spec` y `db.sqlite3`. Ningún módulo,
> recurso o carpeta de contenido debe llamarse así, o Git lo omitiría en silencio.

## 5. Responsabilidades de los módulos

| Módulo | Responsabilidad | No debe hacer |
|---|---|---|
| `domain` | Entidades, enums (franja de edad, resultado, modo, estilo) y puertos | Importar Flet, SQLAlchemy o MySQL |
| `engine/session` | Ciclo de la partida y del turno | Saber si el modo es ruleta o tablero |
| `engine/selector` | Elegir preguntas por categoría, edad y dificultad del jugador, con respaldo | Usar `ORDER BY RAND()` |
| `engine/scoring` | +1 por correcta, 0 en el resto | Depender de dificultad, tiempo o ayudas |
| `engine/helps` | Cambio de pregunta y pista | Consumir turnos |
| `engine/clock` | Reloj monótono inyectable | Depender de la interfaz |
| `engine/modes` | Decidir la categoría de cada turno y el orden de juego | Puntuar |
| `engine/rules` | Condición de victoria y estilo (competitivo; cooperativo después) | Conocer la interfaz |
| `analytics` | Resultados y clasificación de competencias a partir de `game_turns` | Guardar tablas de caché en el MVP |
| `packages` | Validar, importar (idempotente) y exportar paquetes JSON | Generar preguntas con IA |
| `persistence` | ORM, repositorios, migraciones, comprobación de conexión | Contener lógica de juego |
| `ui` | Vistas y navegación; dibuja el cronómetro | **Decidir** cuándo vence el tiempo o aplicar reglas |
| `config` | Cargar y validar la configuración (entorno y `.env`) | Registrar o mostrar contraseñas |

## 6. Reglas de juego

### 6.1 Puntuación y victoria
- Correcta: **+1**. Incorrecta, omitida o tiempo agotado: **0**.
- La puntuación no depende de la dificultad, el tiempo ni las ayudas.
- Gana quien tenga más puntos. En caso de empate, victoria compartida.
- Como cada jugador recibe preguntas de su propia franja y dificultad, el +1 uniforme mantiene
  la partida equilibrada en familias con edades mixtas.

### 6.2 Turno
```
Inicio de turno (cambios usados = 0, pista disponible)
→ la ruleta elige la categoría
→ se muestra la pregunta y arranca el temporizador
→ [cambiar pregunta] vuelve a "se muestra la pregunta"
→ [pista] elimina dos alternativas incorrectas
→ responder | omitir | tiempo agotado
→ explicación (retroalimentación)
→ fin de turno, siguiente jugador
```
Resultados posibles: `correct`, `incorrect`, `skipped`, `timed_out`. Un turno consume
exactamente una pregunta respondida, omitida o vencida; los cambios no consumen turno.

### 6.3 Cambio de pregunta
- Máximo **3 por participante y por turno**. El contador vuelve a 0 al comenzar su siguiente
  turno; no se acumula.
- La pregunta nueva es de la misma categoría y respeta la edad y la dificultad del jugador. La
  descartada no reaparece en esa partida.
- **El temporizador se reinicia** con la pregunta nueva.
- No puntúa ni cuenta como omitida. Cada cambio se registra en `turn_swaps`.
- El botón se deshabilita si no hay otra pregunta elegible.
- El límite se aplica en el motor y, como tope, en la base de datos (`CHECK seq BETWEEN 1 AND 3`).

### 6.4 Pista
- Opción de partida `hint_per_turn`: **0 (desactivada, valor por defecto)** o **1** (máximo una
  por turno).
- Elimina **dos alternativas incorrectas**, elegidas con el generador aleatorio sembrado de la
  partida. Solo está disponible en preguntas con **4 o más alternativas**: con 3 la pista
  dejaría únicamente la respuesta correcta, y el verdadero/falso queda excluido.
- Sin penalización de puntos. Se guardan los ids eliminados.
- **Una respuesta dada con pista no cuenta como evaluable** para fortalezas y competencias.
- No detiene el temporizador. Si se cambia de pregunta después de usar la pista, esta ya se
  consumió.

### 6.5 Temporizador
- Opciones: **10, 15, 20, 30 y 45 segundos**, configurables **por jugador**.
- Valores sugeridos al elegir la franja (editables): 4-6 → 45 s; 7-9 → 30 s; resto → 20 s.
- El vencimiento lo decide el motor comparando marcas de un **reloj monótono**; si la interfaz
  se retrasa, el resultado no cambia. `response_ms` mide desde que se muestra la pregunta
  hasta la respuesta.

### 6.6 Franjas de edad
`4-6`, `7-9`, `10-12`, `13-15`, `16-17` y `18+` (equivalentes a los rangos de años 4–6, 7–9,
10–12, 13–15, 16–17 y 18–99). Una pregunta guarda `age_min` y `age_max` en años y es elegible
para una franja si ambos rangos se solapan. La edad es una restricción **dura**; la dificultad
es **blanda**. Se guarda la franja, no la fecha de nacimiento.

## 7. Selección de preguntas y analítica

### 7.1 Selección
1. Se filtran por categoría, estado `published`, idioma, solapamiento de edad y dificultad
   exacta, excluyendo las ya vistas en la partida y las descartadas por cambio.
2. Si no hay candidatas, la dificultad se amplía a ±1 y luego a ±2 (dentro de 1 a 3 en el MVP).
3. Si el conjunto se agota, se permiten repeticiones eligiendo las menos recientes del jugador.
4. Si aun así no hay ninguna que cumpla la edad, el motor lo informa y la interfaz lo muestra.
   **Nunca se sirve una pregunta fuera de la franja.**

Se usa el índice compuesto y muestreo sobre el subconjunto filtrado, nunca `ORDER BY RAND()`.

### 7.2 Resultados y clasificación
- **Por jugador y partida:** puntuación, aciertos, errores, omitidas, tiempos agotados y tiempo
  medio de respuesta.
- **Respuesta evaluable:** resultado `correct` o `incorrect` **y sin pista**. Las omitidas y los
  tiempos agotados no cuentan.
- **Clasificación por competencia:** se calcula sobre el **historial acumulado** del jugador y
  exige **al menos 5 respuestas evaluables** en esa competencia. Con menos, se muestra
  "datos insuficientes".
- **Umbrales por defecto (configurables):** 80 % o más → fortaleza; 50 % o menos → competencia
  por reforzar; el resto → en progreso.
- Limitación conocida: el MVP no pondera la dificultad al clasificar.
- Expectativa realista: con 4 competencias de Matemáticas, el niño necesitará varias partidas
  antes de que cada competencia alcance las 5 respuestas evaluables. La pantalla de una
  partida muestra siempre las cifras de esa partida y solo clasifica cuando el acumulado lo
  permite.

## 8. Banco inicial de prueba

Entre **40 y 60 preguntas propias, validadas y con explicación**, entregadas como paquetes JSON.

**Distribución propuesta (56 preguntas; se confirmará al crear el banco):**

| Categoría | Competencias | Total | 7-9 | 18+ |
|---|---|---|---|---|
| Matemáticas | 4 (numeración y cálculo; multiplicar y dividir; fracciones y medidas; geometría y razonamiento) | 20 | 12 | 8 |
| Lengua y lectura | 2 | 12 | 6 | 6 |
| Ciencias y naturaleza | 2 | 12 | 6 | 6 |
| Cultura general | 2 | 12 | 6 | 6 |
| **Total** | 10 | **56** | **30** | **26** |

Notas:
- Dificultades 1 a 3 en cada franja (el esquema admite hasta 5).
- Los adultos necesitan un volumen comparable al del niño en cada categoría, porque la ruleta
  elige la categoría y cada jugador recibe una pregunta de su propia franja. Con tres jugadores,
  los adultos consumen más preguntas en total que el niño.
- Punto abierto para el diseño de la ruleta (no se implementa ahora): un peso de categoría
  configurable para que Matemáticas salga con más frecuencia sin cambiar las reglas.

## 9. Funcionamiento sin internet

Funciona sin conexión mientras el **servidor MySQL local esté disponible**.

- Fuentes, imágenes e iconos van en `assets/`. Sin CDN, telemetría ni llamadas externas en
  ejecución.
- MySQL escucha solo en `127.0.0.1`, con un usuario propio de la aplicación (no `root`) y
  privilegios mínimos sobre el esquema de SABERIA.
- Al arrancar, la aplicación comprueba la conexión y muestra un diagnóstico con reintento
  (servicio detenido, credenciales, base inexistente, versión no soportada).
- Fechas en UTC.
- La instalación de dependencias necesita red una vez. Ninguna función del MVP requiere IA en
  línea.
- Pendiente de verificar en el equipo de desarrollo: que Flet no descargue componentes en el
  primer arranque.

## 9.1 Requisitos de MySQL

MySQL **8.0.16 o superior** (las restricciones `CHECK` se ignoran en silencio en versiones
anteriores). MariaDB no está soportada. `database.py` lo comprueba al arrancar.

## 10. Alcance exacto del MVP

**Incluye**
- Perfiles de jugador (2 a 8 soportados; pruebas con 2 a 4) con franja de edad, dificultad (1–3)
  y temporizador por jugador.
- **Modo ruleta competitivo** con número de rondas configurable.
- Opción múltiple con explicación tras responder, omitir, imagen opcional, cambio de pregunta y
  pista opcional.
- Puntuación +1 / 0.
- Resultados y perfil acumulado según la sección 7.2.
- Importación y exportación de paquetes JSON con validación.
- Banco de 40–60 preguntas propias (sección 8).
- Prueba completa con la red desconectada.

**No incluye:** tablero (fase 2), modo cooperativo, generación con IA dentro de la aplicación,
importación de fuentes abiertas, editor o administración de preguntas, voz o sonido, reanudar
partidas, empaquetado e instalador, carga masiva del banco.

**Criterio de aceptación:** una partida de ruleta de 2 a 4 jugadores, de principio a fin y con
la red desconectada, que guarde resultados correctos y los muestre, incluyendo cambio de
pregunta, temporizador y perfil acumulado.

## 11. Orden de implementación

| # | Paso | Estado |
|---|---|---|
| 0 | Verificar el entorno local: Python, Flet (también sin red tras instalarlo), MySQL 8.0.16+, usuario de base de datos propio | Pendiente (en el equipo de desarrollo) |
| 1 | Andamiaje: `pyproject.toml`, configuración, ventana mínima y diagnóstico de la base de datos | **Hecho en esta entrega** |
| 2 | Dominio y enums, con pruebas | Pendiente |
| 3 | Persistencia: ORM, migración inicial, repositorios y pruebas de integración | Pendiente |
| 4 | Paquetes JSON: esquema, validador, importador, exportador y banco inicial | Pendiente |
| 5 | Motor: reloj, selector, puntuación, ayudas, máquina de estados y ruleta | Pendiente |
| 6 | Interfaz de la ruleta. **Hito:** partida de 2 jugadores completa | Pendiente |
| 7 | Analítica y pantalla de resultados | Pendiente |
| 8 | Interfaz de la pista y su activación | Pendiente |
| 9 | Pruebas con 2 a 4 jugadores y prueba sin conexión | Pendiente |

Línea de corte: si el tiempo se agota, la interfaz de la pista (paso 8) se difiere primero.
**Fase 2:** `BoardMode` y su vista, definición del tablero en JSON y reglas del cooperativo.

## 12. Riesgos técnicos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Servidor MySQL detenido o mal configurado en el equipo familiar | Alto | Diagnóstico al arrancar, usuario dedicado y documentación |
| Flet descarga componentes en el primer arranque y rompe el uso sin conexión | Medio-alto | Verificarlo en el paso 0; documentar instalación desde caché local |
| La API de Flet cambia entre versiones | Medio | Versión acotada en `pyproject.toml`; el código evita APIs inestables |
| Banco pequeño: repeticiones y celdas vacías | Medio-alto | Concentrar preguntas en 7-9 y 18+, política de respaldo, mensajes claros |
| Umbral de 5 respuestas rara vez alcanzado | Medio | Clasificación sobre el acumulado y "datos insuficientes" visible |
| Abuso del cambio de pregunta o de la pista | Medio | Límite por turno, pista desactivada por defecto y registro para medirlos |
| Tiempo medido con la latencia de la interfaz | Medio | Reloj monótono en el motor y pregunta precargada |
| `CHECK` ignorados en MySQL anterior a 8.0.16 | Medio | Comprobar versión al arrancar y validar también en el motor |
| Portabilidad si la distribución final no admite MySQL | Medio | SQL portable, PyMySQL en Python puro y repositorios tras interfaces |
| Autenticación de MySQL 8 con PyMySQL | Medio | Dependencia `PyMySQL[rsa]` (instala `cryptography`) |
| Calidad del contenido | Alto | Preguntas propias revisadas, con explicación obligatoria |
| Privacidad de menores | Medio | Todo local, solo franja de edad, perfiles archivables, paquetes sin datos de jugadores |
| Ampliación del alcance | Medio | Hito intermedio tras la ruleta; tablero fuera del MVP |

## 13. Supuestos adoptados

- Tiempo agotado y omitida no son evaluables.
- La pista queda fuera del cálculo de fortalezas y competencias.
- Umbrales: 80 % fortaleza, 50 % o menos por reforzar, 5 respuestas mínimas.
- El temporizador se reinicia al cambiar de pregunta.
- Empate: victoria compartida.
- Los resultados educativos se calculan sobre el historial acumulado.
- Temporizador por jugador con valores sugeridos por franja.

## 14. Flujo de trabajo en Git

- La rama por defecto actual del repositorio se llama `https/github.com/JNEON/SABERIA` (nombre
  inusual, probablemente un error al crear el repositorio). **No se ha renombrado**; conviene
  renombrarla a `main` antes de integrar cambios.
- Los cambios se desarrollan en ramas independientes (`feature/...`) y se revisan antes de
  integrarse. Nada se integra directamente en la rama por defecto.
