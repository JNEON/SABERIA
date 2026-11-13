# SABERIA — Plan operativo del MVP

## Estrategia adoptada

- **Modalidad:** desarrollo integral por módulos funcionales.
- **Responsable técnico principal:** ChatGPT como arquitecto, implementador asistido y revisor de coherencia.
- **Otras IA:** no se incorporan por ahora. Se reconsiderarán solo ante una necesidad concreta.
- **Prioridad:** terminar primero un MVP jugable.
- **Forma de trabajo:** diseño breve → implementación completa → pruebas → verificación → documentación de cierre.

## 1. Definición de terminado para el MVP

El MVP se considera terminado cuando una persona puede, sin conexión a Internet:

1. Abrir SABERIA.
2. Configurar una partida para 2–4 jugadores.
3. Seleccionar o registrar jugadores.
4. Iniciar una partida con preguntas locales.
5. Responder dentro del tiempo establecido.
6. Usar las ayudas permitidas conforme a las reglas.
7. Completar los turnos sin repetir preguntas dentro de la partida.
8. Ver puntuaciones y resultados por jugador.
9. Consultar preguntas falladas y sus explicaciones.
10. Cerrar la partida y volver a iniciar otra sin corromper datos.

La ampliación a 2–8 jugadores puede conservarse como objetivo de escalabilidad, pero el primer MVP se valida con 2–4 jugadores.

## 2. Fases y entregables

### Fase 0 — Línea base y documentación
**Estado:** iniciada con este paquete documental.

Entregables:
- estado técnico;
- arquitectura;
- decisiones;
- reglas del juego;
- modelo de datos;
- plan operativo;
- protocolo de trabajo.

Criterio de salida: documentación revisada y discrepancias marcadas como pendientes, no resueltas por suposición.

### Fase 1 — Banco de preguntas mínimo utilizable
Entregables:
- paquete JSON de Ciencias Naturales con las 35 preguntas aprobadas;
- validación de esquema;
- pruebas del paquete;
- metadatos de fuente, licencia interna y versión.

Criterios:
- 35 preguntas, sin sustituciones inventadas;
- códigos de categoría, tema y competencia consistentes;
- exactamente una opción correcta en preguntas de selección única;
- dos opciones para verdadero/falso;
- edades y dificultad válidas;
- explicaciones presentes;
- paquete reproducible y verificable.

### Fase 2 — Importación y persistencia de contenido
Entregables:
- servicio de importación;
- cálculo de checksum SHA-256;
- validación completa antes de persistir;
- transacción atómica;
- detección idempotente de paquete/version/contenido repetido;
- reporte de errores por registro y campo.

Criterios:
- si existe un error, no se importa parcialmente;
- si todo es válido, se importa y publica según las reglas aprobadas;
- reimportar el mismo paquete no duplica contenido;
- la operación no modifica datos ajenos al paquete;
- pruebas con base de datos de prueba antes de usar la base local.

### Fase 3 — Dominio y motor de juego
Entregables:
- servicios de aplicación para crear partida, jugadores, turnos, seleccionar pregunta, registrar respuesta y finalizar partida;
- repositorios SQLAlchemy;
- control de temporizador;
- ayudas y cambios de pregunta;
- prevención de repetición dentro de la partida.

Criterios:
- reglas centralizadas en dominio/servicios, no dispersas en widgets;
- transiciones de estado válidas;
- persistencia consistente de cada turno;
- pruebas unitarias e integración para casos normales y límites.

### Fase 4 — Interfaz Flet del MVP
Entregables:
- pantalla de inicio;
- configuración de partida;
- selección/registro de jugadores;
- pantalla de juego;
- temporizador y acciones;
- pantalla de resultados.

Criterios:
- interfaz utilizable sin Internet;
- estado visual coherente con el estado del juego;
- no duplicar lógica de negocio en la interfaz;
- errores de persistencia comunicados sin perder el estado de la partida.

### Fase 5 — Resultados y aprendizaje
Entregables:
- tabla de puntuación;
- correctas, incorrectas, omitidas y agotadas por tiempo;
- porcentaje y tiempo promedio;
- preguntas falladas con explicación;
- fortalezas y aspectos por reforzar cuando se cumpla el mínimo de evidencia.

Criterios:
- no generar conclusiones de competencia con menos de cinco respuestas evaluables;
- omitidas y agotadas por tiempo no cuentan como evidencia evaluable;
- respuestas correctas con ayuda no cuentan para el análisis de dominio;
- mensajes educativos, no diagnósticos.

### Fase 6 — Pruebas integrales y empaquetado
Entregables:
- escenario de partida completa;
- verificación offline;
- instrucciones de instalación/ejecución;
- procedimiento de copia de seguridad;
- versión candidata del MVP.

Criterio de salida: partida completa desde configuración hasta resultados, reproducible y probada.

## 3. Orden de prioridad

1. Evitar ampliar alcance antes de cerrar una partida funcional.
2. Resolver primero bloqueos que impidan ejecutar el flujo completo.
3. Mantener el banco inicial suficiente para probar el motor.
4. Posponer FastAPI, funciones online, analítica avanzada y ampliaciones no esenciales.
5. No construir funcionalidades administrativas complejas antes de validar el juego local.

## 4. Gestión de cambios

Cada solicitud nueva se clasifica como:
- **Bloqueante MVP:** impide completar el flujo básico.
- **Necesaria MVP:** mejora seguridad, consistencia o usabilidad esencial.
- **Posterior al MVP:** se registra en backlog, no interrumpe la fase actual.

No se incorporan dependencias nuevas sin justificar necesidad, mantenimiento y compatibilidad.
