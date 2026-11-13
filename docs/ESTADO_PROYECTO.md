# SABERIA — Estado del proyecto

**Documento de referencia:** estado inicial de trabajo integral para el MVP.  
**Repositorio local conocido:** `C:\xampp\htdocs\xampp\SABERIA`  
**Rama de trabajo registrada:** `feature/v0.1-mvp`  
**Última verificación comunicada:** 13 de noviembre de 2026.

## 1. Objetivo

SABERIA es un juego educativo familiar, offline y en español. Su primera versión debe permitir configurar una partida, jugar turnos con preguntas de un banco local, aplicar reglas consistentes de puntuación y mostrar resultados educativos al finalizar.

## 2. Estado técnico confirmado por el usuario

- Suite completa: **101 passed, 4 skipped**.
- Ruff: **All checks passed**.
- El módulo de contenidos compila con `python -m compileall .\src\saberia\content`.
- `src/saberia/content/schema.py`, `validator.py` y `package_loader.py` existen.
- `tests/test_content.py` contiene 23 pruebas.
- `tests/test_package_loader.py` contiene 4 pruebas.
- La corrección de importaciones Ruff se aplicó en `tests/test_persistence_integration.py`.
- El cargador JSON lee archivos, convierte el JSON, ejecuta el validador y devuelve los datos validados. No escribe en MariaDB.

## 3. Base de datos y migraciones

Contexto técnico previamente verificado:

- MariaDB 10.4.32 de XAMPP.
- Base de datos: `saberiadb`.
- Usuario de aplicación limitado a `saberiadb.*` en `127.0.0.1`.
- Alembic reportado en revisión `7c367e79f877 (head)`.
- `alembic check` reportó que no había operaciones nuevas de migración.
- Se registraron 13 tablas: `alembic_version`, `categories`, `competencies`, `game_players`, `game_turns`, `games`, `players`, `question_options`, `question_packages`, `question_sources`, `questions`, `topics`, `turn_swaps`.
- No ejecutar migraciones, reinicios, borrados ni importaciones de datos sin revisión explícita.

Estos datos deben verificarse de nuevo si se cambia el entorno o la rama.

## 4. Componentes de contenido

Estado conocido:

- Contrato de datos: `src/saberia/content/schema.py`.
- Validador: `src/saberia/content/validator.py`.
- Cargador JSON: `src/saberia/content/package_loader.py`.
- Pruebas: `tests/test_content.py` y `tests/test_package_loader.py`.
- Directorio de paquetes: `src/saberia/packages/examples/`.

El cargador no persiste información. La importación transaccional, idempotencia, checksum y publicación siguen siendo trabajo futuro.

## 5. Banco inicial de preguntas

Se aprobaron editorialmente **35 preguntas de Ciencias Naturales**, distribuidas así:

| Preguntas | Rango de edad |
|---|---:|
| 1–5 | 4–6 |
| 6–10 | 7–9 |
| 11–15 | 8–10 |
| 16–20 | 10–12 |
| 21–25 | 13–15 |
| 26–30 | 16–17 |
| 31–35 | 18+ |

La aprobación editorial está confirmada. Sin embargo, el registro disponible no contiene necesariamente el texto literal completo de todos los enunciados, opciones y explicaciones. No reconstruir esos campos por inferencia ni afirmar que un paquete está completo hasta verificar el contenido literal.

## 6. Pendientes principales

1. Consolidar el contenido literal de las 35 preguntas en un paquete JSON válido.
2. Añadir pruebas específicas del paquete real y de sus metadatos.
3. Diseñar e implementar importación transaccional e idempotente, con revisión previa.
4. Implementar repositorios y servicios de aplicación.
5. Implementar motor de juego y pruebas de reglas.
6. Construir interfaz Flet del MVP.
7. Implementar resultados y resumen educativo.
8. Ejecutar pruebas integrales de una partida completa.
9. Documentar instalación, ejecución y recuperación local.

## 7. Regla de actualización

Al cerrar cada módulo, actualizar este documento con:
- archivos creados/modificados;
- pruebas ejecutadas y resultado exacto;
- migraciones realizadas, si las hubo;
- decisiones nuevas;
- pendientes y riesgos;
- fecha de verificación.
