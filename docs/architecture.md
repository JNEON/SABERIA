# SABERIA --- Arquitectura del sistema

> **Versión documental 2.0 --- actualización de estado y estructura.**
>
> Este documento conserva las decisiones funcionales y de arquitectura
> del diseño aprobado, y actualiza las responsabilidades de los módulos
> y el estado conocido de implementación.
>
> **Estado:** dominio, persistencia ORM, migraciones y módulo de
> lectura/validación de paquetes JSON implementados. El MVP jugable
> todavía está en desarrollo.
>
> Documentos relacionados: [data-model.md](data-model.md) ·
> [question-package-format.md](question-package-format.md)

## 1. Contexto y objetivos

SABERIA es un videojuego educativo familiar de preguntas y aprendizaje.
Se desarrolla primero para escritorio, con una arquitectura que permita
evolucionar posteriormente a web y dispositivos móviles.

### 1.1 Familia de prueba del MVP

Las primeras pruebas se plantean con un niño de 9 años y dos adultos
mayores de 30.

-   Franjas principales de prueba: **7-9** y **18+**.
-   Objetivo educativo para el niño: mejorar en Matemáticas y reforzar
    conocimientos en otras áreas.
-   La edad determina qué preguntas son elegibles.
-   La dificultad y el temporizador se configuran de manera
    independiente por jugador.
-   El perfil acumulado por competencia será el principal mecanismo de
    seguimiento del aprendizaje.

## 2. Decisiones de arquitectura

  -----------------------------------------------------------------------
  Tema                                Decisión
  ----------------------------------- -----------------------------------
  Plataforma inicial                  Escritorio; arquitectura preparada
                                      para una evolución posterior

  Lenguaje                            Python

  Interfaz prevista                   Flet

  Participantes                       De 2 a 8 soportados por el modelo;
                                      pruebas iniciales de 2 a 4

  Modalidades                         Ruleta primero; tablero en fase
                                      posterior

  Estilo                              Competitivo primero; cooperativo
                                      después

  Preguntas                           Contenido propio, fuentes abiertas
                                      con licencia compatible y contenido
                                      asistido por IA con validación
                                      humana

  Persistencia                        MariaDB 10.4.32 en el entorno local
                                      actual

  ORM                                 SQLAlchemy 2

  Migraciones                         Alembic

  Driver                              PyMySQL

  Intercambio de contenido            Paquetes JSON

  Conectividad                        La partida debe funcionar sin
                                      Internet mientras MariaDB local
                                      esté disponible
  -----------------------------------------------------------------------

El banco inicial del MVP se concibió entre 40 y 60 preguntas propias. El
paquete de Ciencias Naturales con 35 preguntas aprobadas editorialmente
constituye el primer paquete de contenido; no reemplaza por sí solo el
objetivo general del banco mínimo.

## 3. Principios

-   Separación entre dominio, persistencia, contenido, motor de juego,
    analítica e interfaz.
-   El dominio no importa Flet, SQLAlchemy ni el driver de base de
    datos.
-   El motor de juego no conoce los detalles de la interfaz.
-   La interfaz presenta el estado y solicita acciones; no decide las
    reglas.
-   La persistencia concentra el acceso a MariaDB.
-   El contenido se intercambia mediante paquetes JSON validados.
-   La validación de un paquete no equivale a importarlo o publicarlo en
    la base de datos.
-   Las reglas que involucran varias entidades o filas se validan en la
    capa de aplicación o dominio.
-   No se requiere conexión a servicios externos durante una partida.

## 4. Estructura del proyecto

La siguiente estructura refleja las responsabilidades conocidas del
proyecto. Los módulos que aún no se han implementado se identifican como
pendientes en la sección 10.

``` text
SABERIA/
├── pyproject.toml
├── .env.example
├── README.md
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   └── question-package-format.md
├── src/
│   └── saberia/
│       ├── main.py
│       ├── __main__.py
│       ├── config/
│       ├── content/
│       │   ├── __init__.py
│       │   ├── schema.py
│       │   ├── validator.py
│       │   └── package_loader.py
│       ├── domain/
│       │   ├── entities.py
│       │   ├── enums.py
│       │   └── rules.py
│       ├── persistence/
│       │   ├── base.py
│       │   ├── database.py
│       │   ├── models/
│       │   └── repositories/
│       ├── packages/
│       │   └── examples/
│       ├── engine/
│       ├── analytics/
│       ├── ui/
│       └── assets/
└── tests/
```

### 4.1 Responsabilidad de los módulos

  -----------------------------------------------------------------------
  Módulo                              Responsabilidad
  ----------------------------------- -----------------------------------
  `config`                            Cargar y validar la configuración
                                      de la aplicación

  `content`                           Definir el contrato JSON, validar
                                      paquetes y leer archivos JSON

  `domain`                            Entidades, enumeraciones y reglas
                                      independientes de la
                                      infraestructura

  `persistence`                       Conexión, modelos ORM, repositorios
                                      y acceso a la base de datos

  `packages`                          Ejemplos y recursos de paquetes de
                                      contenido

  `engine`                            Ciclo de partida, turnos,
                                      selección, puntuación, ayudas y
                                      reloj

  `analytics`                         Resultados y clasificación de
                                      competencias

  `ui`                                Interfaz gráfica y navegación

  `assets`                            Fuentes, imágenes e iconos locales

  `tests`                             Pruebas unitarias y de integración
  -----------------------------------------------------------------------

**Ubicación real del módulo de contenido:** el contrato, el validador y
el cargador JSON están en `src/saberia/content/`. La carpeta
`src/saberia/packages/` no es responsable de implementar esas funciones.

## 5. Arquitectura por capas

### 5.1 Dominio

Contiene entidades, enumeraciones y reglas del negocio que no dependen
de la interfaz ni de la infraestructura. No debe importar Flet,
SQLAlchemy ni PyMySQL.

### 5.2 Persistencia

Gestiona el almacenamiento local mediante SQLAlchemy y MariaDB. Incluye
la base declarativa, los modelos ORM, la configuración de conexión y las
migraciones de Alembic. Los repositorios encapsulan las operaciones de
lectura y escritura que requiera la aplicación.

La existencia de modelos y migraciones no significa que todos los casos
de uso de persistencia estén terminados: la importación de paquetes y
los repositorios del flujo de juego son trabajo pendiente.

### 5.3 Contenido

El módulo `src/saberia/content/` contiene:

-   `schema.py`: contrato de datos, tipos y constantes del paquete.
-   `validator.py`: validaciones estructurales y semánticas.
-   `package_loader.py`: lectura de JSON y ejecución de la validación.

El cargador devuelve los datos de un paquete válido. No realiza por sí
mismo inserciones, actualizaciones ni publicación en MariaDB.

### 5.4 Motor de juego

El motor será responsable de gestionar la partida y los turnos,
seleccionar preguntas elegibles, aplicar puntuación, controlar ayudas y
temporizador, y determinar las condiciones de finalización. Debe poder
probarse sin ejecutar la interfaz gráfica.

### 5.5 Interfaz

La interfaz permitirá configurar jugadores y partidas, presentar la
ruleta, las preguntas, las opciones, el temporizador y los resultados.
Las reglas se aplicarán en el motor y no directamente en los controles
visuales.

### 5.6 Analítica

La analítica calculará resultados por partida y el desempeño acumulado
por competencia. Las respuestas omitidas, los tiempos agotados y las
respuestas realizadas con pista no se consideran evaluables para el
perfil de competencias.

## 6. Reglas de juego

### 6.1 Puntuación y victoria

-   Respuesta correcta: **+1 punto**.
-   Respuesta incorrecta, omitida o tiempo agotado: **0 puntos**.
-   La puntuación no depende de la dificultad, el tiempo ni las ayudas.
-   Gana quien obtiene más puntos. En caso de empate, se declara
    victoria compartida.

### 6.2 Ciclo del turno

``` text
Inicio del turno
→ selección de categoría
→ presentación de pregunta y comienzo del temporizador
→ cambio de pregunta (opcional)
→ uso de pista (opcional)
→ responder | omitir | tiempo agotado
→ explicación y retroalimentación
→ registro del resultado
→ siguiente jugador
```

Resultados persistidos: `correct`, `incorrect`, `skipped` y `timed_out`.

### 6.3 Cambio de pregunta

-   Máximo **3 cambios por participante y por turno**.
-   El contador vuelve a cero al comenzar el siguiente turno del
    participante.
-   La nueva pregunta conserva la categoría y respeta edad e idioma.
-   La dificultad puede flexibilizarse según la política de selección.
-   La pregunta descartada no debe repetirse durante la misma partida.
-   El temporizador se reinicia con la pregunta nueva.
-   El cambio no otorga ni resta puntos y queda registrado en
    `turn_swaps`.

### 6.4 Pista

-   Desactivada por defecto.
-   Cuando se habilita, se permite una pista por turno.
-   Elimina dos opciones incorrectas.
-   Solo aplica a preguntas `single_choice` con cuatro o más opciones.
-   No aplica a verdadero/falso.
-   No modifica la puntuación ni detiene el temporizador.
-   Las respuestas realizadas con pista no se consideran evaluables para
    el perfil de competencias.

### 6.5 Temporizador

Opciones previstas: **10, 15, 20, 30 y 45 segundos**, configurables por
jugador.

El vencimiento debe determinarlo el motor con un reloj monótono. La
interfaz solo representa el tiempo restante.

### 6.6 Franjas de edad

  Franja                     Edad
  --------- ---------------------
  `4-6`                     4 a 6
  `7-9`                     7 a 9
  `10-12`                 10 a 12
  `13-15`                 13 a 15
  `16-17`                 16 a 17
  `18+`       18 años en adelante

Las preguntas almacenan `age_min` y `age_max`. Cuando `age_max` es
`null`, no existe límite superior. La elegibilidad se determina por el
solapamiento entre el rango de la pregunta y el rango del jugador. La
edad es una restricción obligatoria; la dificultad puede flexibilizarse
si no hay preguntas disponibles.

El rango editorial 8-10 utilizado en el primer paquete de Ciencias
Naturales no crea una nueva franja del dominio: se representa mediante
los límites individuales de cada pregunta.

## 7. Selección de preguntas y analítica

### 7.1 Selección

1.  Filtrar por categoría, estado publicado, idioma, rango de edad y
    dificultad solicitada.
2.  Excluir las preguntas ya utilizadas o descartadas durante la
    partida.
3.  Si no hay candidatas, ampliar la dificultad según la política del
    motor, sin relajar la edad.
4.  Si no existen preguntas elegibles por edad, informar que no hay
    contenido disponible.

No se deben seleccionar preguntas fuera de la franja del jugador.

### 7.2 Resultados y clasificación

Por jugador y partida se registrarán puntuación, aciertos, errores,
omitidas, tiempos agotados y tiempo de respuesta.

Una respuesta evaluable es `correct` o `incorrect` y no debe haber
utilizado pista. La clasificación por competencia requiere al menos
cinco respuestas evaluables acumuladas:

-   80 % o más: fortaleza.
-   50 % o menos: competencia por reforzar.
-   Entre ambos valores: en progreso.
-   Menos de cinco respuestas: datos insuficientes.

## 8. Banco inicial de preguntas

El diseño aprobado contempló un banco de **40 a 60 preguntas propias**,
con explicación, clasificación académica y adaptación por edad. La
distribución inicial propuesta fue:

  Categoría                 Competencias   Total propuesto      7-9      18+
  ----------------------- -------------- ----------------- -------- --------
  Matemáticas                          4                20       12        8
  Lengua y lectura                     2                12        6        6
  Ciencias y naturaleza                2                12        6        6
  Cultura general                      2                12        6        6
  **Total**                       **10**            **56**   **30**   **26**

Esta tabla representa la distribución propuesta originalmente, no el
inventario actual.

### 8.1 Primer paquete aprobado

El primer paquete editorial aprobado es **Ciencias Naturales**, con **35
preguntas**. Se revisó por siete rangos editoriales:

-   4-6
-   7-9
-   8-10
-   10-12
-   13-15
-   16-17
-   18+

El rango 8-10 es una clasificación editorial y se expresa mediante
`age_min` y `age_max`. Este paquete es el primer conjunto de contenido
aprobado y no sustituye el objetivo de completar el banco mínimo general
del MVP.

## 9. Funcionamiento sin Internet

SABERIA está diseñada para funcionar sin conexión a Internet durante las
partidas, siempre que el servidor MariaDB local esté disponible.

-   Los recursos visuales deben almacenarse localmente.
-   No se requieren servicios externos durante la ejecución.
-   No se requiere IA en línea para jugar.
-   La instalación inicial de dependencias puede requerir Internet.
-   Las credenciales se cargan desde la configuración local y no deben
    exponerse en registros.

## 10. Estado de implementación

El estado se refiere a la implementación conocida y probada en el
repositorio durante la actualización de este documento. No debe
interpretarse como aceptación final del MVP.

  -----------------------------------------------------------------------
  Componente                          Estado
  ----------------------------------- -----------------------------------
  Configuración Python y entorno      Implementado
  virtual                             

  Conexión con MariaDB 10.4.32        Configurada y verificada

  Base de datos `saberiadb`           Configurada

  Migraciones Alembic                 Implementadas y aplicadas

  Modelos ORM                         Implementados (12 modelos)

  Entidades, enumeraciones y reglas   Implementadas
  de dominio                          

  Pruebas automatizadas existentes    101 aprobadas y 4 omitidas en la
                                      última ejecución reportada

  Contrato de paquetes JSON           Implementado

  Validador de paquetes JSON          Implementado

  Cargador de paquetes JSON           Implementado

  Paquete de Ciencias Naturales       35 preguntas aprobadas
                                      editorialmente

  Repositorios de persistencia        Pendiente de completar

  Importación transaccional JSON a    Pendiente
  MariaDB                             

  Exportación JSON desde la base de   Pendiente
  datos                               

  Motor de juego completo             Pendiente

  Ruleta funcional                    Pendiente

  Interfaz completa de partida        Pendiente

  Analítica integrada en la interfaz  Pendiente

  Prueba integral del MVP sin         Pendiente
  Internet                            
  -----------------------------------------------------------------------

Los resultados de pruebas indicados corresponden a la última ejecución
comunicada y deben actualizarse cuando se realice una nueva ejecución.

## 11. Alcance del MVP

### Incluye

-   Perfiles de 2 a 8 jugadores en el modelo; pruebas iniciales con 2 a
    4.
-   Configuración de franja de edad, dificultad y temporizador por
    jugador.
-   Modo ruleta competitivo.
-   Preguntas de selección única y verdadero/falso.
-   Explicación después de responder.
-   Cambio de pregunta y pista opcional.
-   Puntuación +1 / 0.
-   Registro de resultados.
-   Perfil acumulado por competencia.
-   Validación de paquetes de preguntas.
-   Importación y exportación de paquetes JSON cuando se complete el
    módulo correspondiente.
-   Funcionamiento sin Internet durante la partida.

### Fuera del MVP

-   Tablero.
-   Modo cooperativo.
-   Generación de preguntas con IA dentro de la aplicación.
-   Sincronización en la nube y API remota.
-   Cuentas en línea.
-   Voz y sonido.
-   Funciones administrativas avanzadas de edición de preguntas.

### Criterio de aceptación

Una partida de ruleta completa con dos a cuatro participantes, desde la
configuración hasta los resultados, que funcione sin Internet, respete
las reglas de edad y dificultad, registre los turnos y presente
puntuación y resultados.

## 12. Orden de desarrollo pendiente

1.  Completar los repositorios necesarios para los casos de uso del MVP.
2.  Diseñar e implementar la importación transaccional e idempotente de
    paquetes JSON.
3.  Implementar la exportación de paquetes.
4.  Completar pruebas de integración de persistencia.
5.  Implementar el selector de preguntas.
6.  Implementar el ciclo de turnos, puntuación y reloj.
7.  Implementar cambios de pregunta y pistas.
8.  Implementar la ruleta.
9.  Construir la interfaz de partida.
10. Integrar resultados y analítica.
11. Ejecutar pruebas integrales con dos a cuatro participantes.
12. Verificar el funcionamiento sin conexión.

## 13. Riesgos técnicos

  -----------------------------------------------------------------------
  Riesgo                              Mitigación
  ----------------------------------- -----------------------------------
  MariaDB no disponible               Diagnóstico de conexión y guía de
                                      instalación

  Paquete JSON inválido               Validar antes de iniciar cualquier
                                      importación

  Preguntas insuficientes por edad    Ampliar contenido; nunca relajar la
                                      edad

  Repetición de preguntas             Registrar preguntas utilizadas y
                                      descartadas

  Reglas dentro de la interfaz        Mantener el motor independiente y
                                      probarlo

  Contenido ambiguo o incorrecto      Revisión editorial y explicación
                                      obligatoria

  Exposición de datos de menores      Funcionamiento local y
                                      almacenamiento de franja, no fecha
                                      de nacimiento

  Crecimiento del alcance             Priorizar el MVP jugable y diferir
                                      fase 2
  -----------------------------------------------------------------------

## 14. Flujo de trabajo

Cada módulo de desarrollo debe incluir implementación completa de la
funcionalidad acordada, pruebas automatizadas, validación de calidad,
documentación actualizada y criterios de aceptación verificables. Los
cambios se revisan y prueban antes de integrarse en la rama principal.
