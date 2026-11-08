# SABERIA — Formato de paquetes de preguntas (JSON)

> **Versión 1 del formato (`format_version: 1`).** Este documento define el contrato. El esquema
> formal (`content/schema/`), el validador, el importador y el exportador **aún no están
> implementados** (paso 4 del plan de implementación).
> Ver también: [data-model.md](data-model.md) · [architecture.md](architecture.md)

## 1. Propósito

JSON se usa **solo** para importar y exportar preguntas; la base de datos principal es MySQL.
Todo el contenido (también las preguntas propias) entra por paquetes, de modo que
procedencia, licencia y validación se tratan igual sea cual sea el origen.

Un paquete es un archivo `.json` en UTF-8 que contiene una fuente, categorías, competencias y
preguntas.

## 2. Estructura

```json
{
  "format_version": 1,
  "package": {
    "uid": "6f9c2a3e-8d41-4b7a-9d57-0c1b2a3d4e5f",
    "name": "Banco inicial de prueba",
    "version": "1.0.0",
    "language": "es",
    "created_at": "2026-11-08T00:00:00Z"
  },
  "source": {
    "name": "Preguntas propias de SABERIA",
    "license_code": "LicenseRef-SABERIA-Own",
    "license_url": null,
    "attribution_text": null,
    "url": null
  },
  "categories": [
    { "code": "math", "name": "Matemáticas", "sort_order": 1 }
  ],
  "competencies": [
    {
      "code": "math.add_sub",
      "category": "math",
      "name": "Numeración y cálculo",
      "description": "Suma y resta, valor posicional"
    }
  ],
  "questions": [
    {
      "external_id": "math-0001",
      "category": "math",
      "competency": "math.add_sub",
      "type": "single_choice",
      "prompt": "¿Cuánto es 48 + 27?",
      "explanation": "48 + 27 = 75: 40 + 20 = 60 y 8 + 7 = 15; 60 + 15 = 75.",
      "media": null,
      "age_min": 7,
      "age_max": 9,
      "difficulty": 1,
      "origin": "own",
      "status": "published",
      "validated_by": "Nombre del revisor",
      "validated_at": "2026-11-08T00:00:00Z",
      "options": [
        { "text": "65", "correct": false },
        { "text": "75", "correct": true },
        { "text": "85", "correct": false },
        { "text": "74", "correct": false }
      ]
    }
  ]
}
```

(El ejemplo es ilustrativo; los valores de UUID, fechas y nombre del revisor son de muestra.)

## 3. Campos

### 3.1 Raíz
| Campo | Obligatorio | Descripción |
|---|---|---|
| `format_version` | Sí | Entero. Por ahora `1`. Un formato desconocido se rechaza |
| `package` | Sí | Identidad del paquete |
| `source` | Sí | Procedencia y licencia |
| `categories` | Sí | Categorías usadas por las preguntas |
| `competencies` | Sí | Competencias usadas por las preguntas |
| `questions` | Sí | Lista de preguntas (puede estar vacía) |

### 3.2 `package`
| Campo | Obligatorio | Regla |
|---|---|---|
| `uid` | Sí | UUID. Identifica el paquete entre versiones |
| `name` | Sí | Hasta 120 caracteres |
| `version` | Sí | Texto de versión (por ejemplo `1.0.0`), hasta 20 caracteres |
| `language` | Sí | Código de idioma (`es`). Todas las preguntas del paquete comparten idioma |
| `created_at` | No | Fecha ISO 8601 en UTC |

### 3.3 `source`
| Campo | Obligatorio | Regla |
|---|---|---|
| `name` | Sí | |
| `license_code` | Sí | SPDX cuando exista (`CC-BY-4.0`, `CC-BY-SA-4.0`, `CC0-1.0`) o `LicenseRef-SABERIA-Own` para contenido propio |
| `license_url` | No | |
| `attribution_text` | Condicional | **Obligatorio** si la licencia exige atribución (familia `CC-BY`) |
| `url` | No | |

### 3.4 `categories` y `competencies`
- `categories[].code`: identificador estable (minúsculas, dígitos, `_`). `name`, `sort_order`.
- `competencies[].code`: identificador estable con prefijo de categoría (`math.add_sub`).
  `category` debe ser un `code` de `categories`.

### 3.5 `questions[]`
| Campo | Obligatorio | Regla |
|---|---|---|
| `external_id` | Sí | Único **dentro del paquete** (hasta 64 caracteres). Es la clave de idempotencia |
| `category` / `competency` | Sí | Códigos definidos en el mismo paquete; la competencia debe pertenecer a la categoría |
| `type` | Sí | `single_choice` (el verdadero/falso es una pregunta de dos opciones) |
| `prompt` | Sí | 1 a 500 caracteres |
| `explanation` | Condicional | 1 a 1000 caracteres. **Obligatoria si `status` es `published`** (retroalimentación educativa) |
| `media` | No | Ruta **relativa** dentro de `assets/` (por ejemplo `media/math/0001.png`). Sin `..`, sin rutas absolutas ni URL |
| `age_min`, `age_max` | Sí | Enteros 4 a 99, con `age_min <= age_max` |
| `difficulty` | Sí | Entero 1 a 5 (el MVP usa 1 a 3) |
| `origin` | Sí | `own`, `open_source` o `ai_assisted` |
| `status` | Sí | `draft`, `validated`, `published` o `retired` |
| `validated_by`, `validated_at` | Condicional | **Obligatorios** si `origin = ai_assisted` y `status = published` |
| `options` | Sí | De 2 a 6 elementos `{ "text", "correct" }` |

## 4. Reglas de validación

El validador debe rechazar el paquete completo (sin importar nada) si hay errores, e informar
**todos** los errores con su ruta (por ejemplo `questions[12].options`), no solo el primero.

1. `format_version` conocido y estructura completa.
2. `external_id` únicos dentro del paquete; códigos de categoría y competencia únicos y
   coherentes entre sí.
3. Cada pregunta tiene **una y solo una** opción correcta, entre 2 y 6 opciones, sin textos
   vacíos ni opciones duplicadas.
4. `age_min <= age_max`, rangos y dificultad dentro de los límites.
5. `explanation` presente en las publicadas; `validated_by` y `validated_at` en las
   `ai_assisted` publicadas.
6. Licencia y, cuando se exija, atribución presentes.
7. `media` solo con rutas relativas seguras.
8. Longitudes máximas respetadas: `prompt` 500, `explanation` 1000, texto de cada opción 255.
9. **Pista:** solo se ofrece en preguntas con **4 o más opciones** (elimina dos incorrectas y deja
   dos). Una pregunta con menos opciones es válida, pero no admite pista.
10. Duplicados: se avisa (no se rechaza) cuando el `content_hash` coincide con otra pregunta ya
    existente.

### 4.1 `content_hash`
SHA-256 del texto normalizado: el `prompt` más las opciones ordenadas alfabéticamente, cada
parte en Unicode NFC, en minúsculas y con espacios colapsados. No depende del orden de las
opciones ni de `external_id`.

## 5. Importación

- **Idempotente.** Un mismo paquete (`uid` + `version` + `checksum_sha256`) importado dos veces
  no duplica nada.
- Mismo `uid` y `version` con checksum distinto: **error** (se debe subir la versión).
- Versión nueva del mismo `uid`: las preguntas cuyo contenido cambió se insertan como
  **versiones nuevas** (`replaces_question_id`) y las anteriores pasan a `retired`. Una pregunta
  publicada nunca se edita en el sitio, para no alterar el historial de partidas.
- Las preguntas `draft` y `validated` se importan pero **nunca se sirven** en una partida; solo
  las `published`.
- La importación es transaccional por paquete. Los paquetes grandes se procesan por lotes
  (se recomienda dividirlos en archivos de unas 5.000 preguntas) para soportar más de 100.000
  preguntas sin cargarlas todas en memoria.
- Las preguntas con `origin = ai_assisted` deben llegar como `draft` y publicarse solo tras la
  validación humana.

## 6. Exportación

El exportador produce un paquete con este mismo formato. **No incluye datos de jugadores ni de
partidas**: solo contenido.

## 7. Banco inicial del MVP

Entre 40 y 60 preguntas propias, validadas y con explicación. Se concentra en las franjas
**7-9** y **18+** (primeras pruebas con un niño de 9 años y dos adultos), con más peso en
Matemáticas. Detalle de la distribución en
[architecture.md](architecture.md#8-banco-inicial-de-prueba).
