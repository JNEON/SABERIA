# SABERIA --- Formato de paquetes de preguntas (JSON)

> **Versión 1.0 del contrato implementado.**
>
> Este documento describe el contrato definido en
> `src/saberia/content/schema.py`. La validación está en
> `src/saberia/content/validator.py` y la lectura de archivos en
> `src/saberia/content/package_loader.py`.
>
> **Importante:** validar y leer un JSON no significa que sus preguntas
> hayan sido importadas a MariaDB ni publicadas.
>
> Documentos relacionados: [data-model.md](data-model.md) ·
> [architecture.md](architecture.md)

## 1. Propósito

SABERIA utiliza paquetes JSON para organizar, validar e intercambiar
preguntas educativas. El paquete es independiente del esquema físico de
MariaDB y contiene metadatos, procedencia, taxonomía y preguntas.

Los archivos se leen como JSON codificado en UTF-8.

## 2. Estructura general

La raíz del paquete contiene exactamente estos componentes:

-   `schema_version`
-   `package`
-   `source`
-   `taxonomy`
-   `questions`

La taxonomía es jerárquica: **categoría → tema → competencia**. Cada
pregunta referencia esa ruta mediante `category_code`, `topic_code` y
`competency_code`.

## 3. Ejemplo conforme al contrato

El siguiente ejemplo ilustra la estructura actual. Los valores son
demostrativos.

``` json
{
  "schema_version": "1.0",
  "package": {
    "package_uid": "6f9c2a3e-8d41-4b7a-9d57-0c1b2a3d4e5f",
    "name": "Ciencias Naturales",
    "version": "1.0.0"
  },
  "source": {
    "name": "SABERIA - Banco interno de preguntas",
    "license_code": "PROPRIETARY_INTERNAL",
    "license_url": null,
    "attribution_text": "Contenido propio del proyecto SABERIA",
    "url": null
  },
  "taxonomy": {
    "categories": [
      {
        "code": "ciencias_naturales",
        "name": "Ciencias Naturales",
        "topics": [
          {
            "code": "seres_vivos",
            "name": "Seres vivos",
            "competencies": [
              {
                "code": "clasificacion_seres_vivos",
                "name": "Clasificación de los seres vivos",
                "description": "Identificación y clasificación de seres vivos"
              }
            ]
          }
        ]
      }
    ]
  },
  "questions": [
    {
      "external_id": "CN-0001",
      "category_code": "ciencias_naturales",
      "topic_code": "seres_vivos",
      "competency_code": "clasificacion_seres_vivos",
      "language": "es",
      "qtype": "single_choice",
      "prompt": "¿Cuál de estos animales es un mamífero?",
      "explanation": "Los mamíferos alimentan a sus crías con leche materna.",
      "age_min": 7,
      "age_max": 9,
      "difficulty": 1,
      "origin": "own",
      "media_path": null,
      "options": [
        {"text": "Rana", "is_correct": false},
        {"text": "Perro", "is_correct": true},
        {"text": "Pez", "is_correct": false},
        {"text": "Mariposa", "is_correct": false}
      ]
    }
  ]
}
```

## 4. Definición de campos

### 4.1 Raíz

  ------------------------------------------------------------------------
  Campo              Tipo              Obligatorio       Descripción
  ------------------ ----------------- ----------------- -----------------
  `schema_version`   texto             Sí                Versión del
                                                         contrato;
                                                         actualmente `1.0`

  `package`          objeto            Sí                Identificación
                                                         del paquete

  `source`           objeto            Sí                Procedencia y
                                                         licencia

  `taxonomy`         objeto            Sí                Taxonomía
                                                         académica

  `questions`        lista             Sí                Preguntas
                                                         incluidas
  ------------------------------------------------------------------------

### 4.2 `package`

  -----------------------------------------------------------------------
  Campo             Tipo              Obligatorio       Regla
  ----------------- ----------------- ----------------- -----------------
  `package_uid`     texto             Sí                Identificador
                                                        UUID

  `name`            texto             Sí                Nombre del
                                                        paquete; máximo
                                                        120 caracteres

  `version`         texto             Sí                Versión con
                                                        formato `X.Y.Z`;
                                                        máximo 20
                                                        caracteres
  -----------------------------------------------------------------------

### 4.3 `source`

  --------------------------------------------------------------------------
  Campo                Tipo              Obligatorio       Regla
  -------------------- ----------------- ----------------- -----------------
  `name`               texto             Sí                Nombre de la
                                                           fuente; máximo
                                                           120 caracteres

  `license_code`       texto             Sí                Código de
                                                           licencia; máximo
                                                           60 caracteres

  `license_url`        texto o `null`    No                URL de la
                                                           licencia; máximo
                                                           255 caracteres

  `attribution_text`   texto o `null`    No                Atribución;
                                                           máximo 500
                                                           caracteres

  `url`                texto o `null`    No                URL de
                                                           procedencia;
                                                           máximo 255
                                                           caracteres
  --------------------------------------------------------------------------

Para el contenido interno del proyecto se ha definido como referencia:

-   `name`: `SABERIA - Banco interno de preguntas`
-   `license_code`: `PROPRIETARY_INTERNAL`
-   `attribution_text`: `Contenido propio del proyecto SABERIA`

### 4.4 `taxonomy`

`taxonomy` contiene una lista `categories`.

Cada categoría contiene:

  Campo      Tipo    Obligatorio     Máximo
  ---------- ------- ------------- --------
  `code`     texto   Sí                  40
  `name`     texto   Sí                  80
  `topics`   lista   Sí                 ---

Cada tema contiene:

  Campo            Tipo             Obligatorio     Máximo
  ---------------- ---------------- ------------- --------
  `code`           texto            Sí                  60
  `name`           texto            Sí                 100
  `competencies`   lista            Sí                 ---
  `description`    texto o `null`   No                 255

Cada competencia contiene:

  Campo           Tipo             Obligatorio     Máximo
  --------------- ---------------- ------------- --------
  `code`          texto            Sí                  60
  `name`          texto            Sí                 100
  `description`   texto o `null`   No                 255

Los códigos se interpretan dentro de su nivel jerárquico. La ruta
completa de una competencia se identifica mediante `category_code`,
`topic_code` y `competency_code`.

### 4.5 `questions[]`

  -------------------------------------------------------------------------
  Campo               Tipo              Obligatorio       Regla
  ------------------- ----------------- ----------------- -----------------
  `external_id`       texto             Sí                Máximo 64
                                                          caracteres; único
                                                          en el paquete

  `category_code`     texto             Sí                Código de
                                                          categoría
                                                          declarado

  `topic_code`        texto             Sí                Código de tema
                                                          perteneciente a
                                                          la categoría

  `competency_code`   texto             Sí                Código de
                                                          competencia
                                                          perteneciente al
                                                          tema

  `language`          texto             Sí                Máximo 8
                                                          caracteres

  `qtype`             texto             Sí                `single_choice` o
                                                          `true_false`

  `prompt`            texto             Sí                Máximo 500
                                                          caracteres

  `explanation`       texto             Sí                Máximo 1000
                                                          caracteres

  `age_min`           entero            Sí                Edad mínima; no
                                                          inferior a 4

  `age_max`           entero o `null`   Sí                Edad máxima;
                                                          `null` significa
                                                          sin límite
                                                          superior

  `difficulty`        entero            Sí                Valor de 1 a 5

  `origin`            texto             Sí                `own`,
                                                          `open_source` o
                                                          `ai_assisted`

  `options`           lista             Sí                Opciones de
                                                          respuesta

  `media_path`        texto o `null`    No                Ruta relativa;
                                                          máximo 255
                                                          caracteres
  -------------------------------------------------------------------------

`external_id` identifica la pregunta dentro del paquete. No es el
identificador numérico de la tabla `questions`.

### 4.6 Tipos de pregunta

  ------------------------------------------------------------------------
  Valor `qtype`         Significado                   Cantidad de opciones
  --------------------- --------------------- ----------------------------
  `single_choice`       Selección de una                          De 2 a 6
                        única respuesta       
                        correcta              

  `true_false`          Verdadero o falso                    Exactamente 2
  ------------------------------------------------------------------------

### 4.7 Opciones

Cada elemento de `options` contiene:

  Campo          Tipo       Obligatorio             Máximo
  -------------- ---------- ------------- ----------------
  `text`         texto      Sí              255 caracteres
  `is_correct`   booleano   Sí                         ---

Cada pregunta debe tener exactamente una opción correcta. Los textos de
las opciones no deben estar vacíos ni repetirse dentro de la pregunta.

## 5. Valores permitidos y reglas

### 5.1 Procedencia

`origin` admite:

-   `own`: contenido propio.
-   `open_source`: contenido procedente de fuentes abiertas.
-   `ai_assisted`: contenido elaborado con asistencia de IA.

La revisión humana y el estado de publicación se gestionan en el flujo
de aplicación y persistencia. No son campos del contrato JSON actual.

### 5.2 Edad

-   `age_min` debe ser un entero igual o superior a 4.
-   `age_max` puede ser un entero o `null`.
-   Cuando `age_max` es un entero, `age_min` no puede superarlo.
-   `age_max: null` representa un límite superior abierto.

Los rangos editoriales de contenido no crean automáticamente nuevas
franjas en el dominio. Por ejemplo, el rango editorial 8-10 se
representa con `age_min: 8` y `age_max: 10`.

### 5.3 Dificultad

    Valor Nivel
  ------- ------------
        1 Muy básica
        2 Básica
        3 Intermedia
        4 Avanzada
        5 Experta

El contrato admite los cinco niveles, aunque el alcance inicial del
juego puede utilizar un subconjunto.

## 6. Límites de longitud

Los límites deben mantenerse sincronizados con `FIELD_LIMITS` en
`schema.py`.

  Campo                         Máximo
  --------------------------- --------
  `package.name`                   120
  `package.version`                 20
  `source.name`                    120
  `source.license_code`             60
  `source.license_url`             255
  `source.attribution_text`        500
  `source.url`                     255
  `category.code`                   40
  `category.name`                   80
  `topic.code`                      60
  `topic.name`                     100
  `topic.description`              255
  `competency.code`                 60
  `competency.name`                100
  `competency.description`         255
  `external_id`                     64
  `language`                         8
  `qtype`                           16
  `prompt`                         500
  `explanation`                   1000
  `media_path`                     255
  `origin`                          16
  `option.text`                    255

## 7. Validación del paquete

El validador de `src/saberia/content/validator.py` comprueba, entre
otros aspectos:

-   Estructura y campos requeridos del paquete.
-   Versión de contrato admitida.
-   Tipos de datos y longitudes máximas.
-   UUID y versión del paquete.
-   Estructura de categoría, tema y competencia.
-   Unicidad de códigos dentro de su ámbito.
-   Correspondencia de la ruta taxonómica de cada pregunta.
-   Identificadores externos no repetidos.
-   Tipo de pregunta permitido.
-   Enunciado y explicación.
-   Rango de edad y dificultad.
-   Procedencia permitida.
-   Cantidad de opciones según el tipo.
-   Existencia de exactamente una opción correcta.
-   Textos de opciones no vacíos ni duplicados.

Los errores deben permitir identificar la ubicación del dato inválido,
por ejemplo `questions[2].age_min` o `questions[4].options`.

## 8. Lectura de paquetes

`src/saberia/content/package_loader.py`:

1.  Recibe la ruta del archivo JSON.
2.  Lee el archivo en UTF-8.
3.  Interpreta el JSON.
4.  Gestiona errores de lectura, decodificación o sintaxis.
5.  Ejecuta `validate_package`.
6.  Informa los errores encontrados.
7.  Devuelve los datos cuando el paquete es válido.

El cargador no escribe registros en MariaDB.

## 9. Campos de persistencia que no pertenecen al JSON actual

El modelo de persistencia contempla campos de control del ciclo de vida
de la pregunta, entre ellos `status`, `validated_by` y `validated_at`.
**Estos campos no forman parte de `QuestionData` en el contrato JSON 1.0
implementado.**

No se deben agregar a un paquete JSON bajo la versión actual. Su
asignación deberá definirse en el servicio de importación/publicación.

En particular, las preguntas `ai_assisted` requieren una política de
validación humana antes de publicarse. La forma de registrar quién
validó y cuándo debe resolverse en la aplicación.

## 10. Relación con la base de datos

La correspondencia conceptual es:

  Contrato JSON                                   Persistencia
  ----------------------------------------------- ---------------------
  `package`                                       `question_packages`
  `source`                                        `question_sources`
  `taxonomy.categories`                           `categories`
  `taxonomy.categories[].topics`                  `topics`
  `taxonomy.categories[].topics[].competencies`   `competencies`
  `questions`                                     `questions`
  `questions[].options`                           `question_options`

La resolución de los códigos de taxonomía a identificadores internos
corresponde al proceso de importación, que es independiente del
validador y cargador actuales.

## 11. Importación y exportación: estado

La validación y lectura JSON están implementadas. La importación
transaccional a MariaDB y la exportación desde la base de datos son
funcionalidades separadas que deben implementarse.

El diseño futuro de importación debe definir, antes de codificarse:

-   Identificación y versionado del paquete.
-   Cálculo y uso del checksum.
-   Idempotencia y tratamiento de paquetes repetidos.
-   Resolución de fuentes y taxonomía.
-   Asignación de estado de pregunta.
-   Validación humana de contenido asistido por IA.
-   Transacción completa o reversión ante errores.
-   Política para preguntas modificadas y versiones anteriores.

Este documento no declara esas operaciones como implementadas.

## 12. Banco inicial

El primer paquete aprobado editorialmente es **Ciencias Naturales**, con
**35 preguntas**. Su clasificación editorial contempla los rangos 4-6,
7-9, 8-10, 10-12, 13-15, 16-17 y 18+.

El rango 8-10 se representa en cada pregunta mediante sus límites de
edad; no es una nueva franja de la enumeración del dominio.

El objetivo general de 40 a 60 preguntas del MVP sigue siendo una meta
de banco total y no debe confundirse con el tamaño del primer paquete.
