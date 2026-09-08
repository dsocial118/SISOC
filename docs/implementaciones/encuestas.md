# Encuestas: rondas, privacidad y resultados

## Alcance

`encuestas` permite crear encuestas periódicas para usuarios autenticados de
SISOC. Una encuesta se publica en rondas; cada ronda abre y cierra en fechas
propias y conserva el resultado histórico de esa versión.

El módulo admite preguntas de texto, opciones, escala, Sí/No, número y fecha.
Las preguntas pueden ser obligatorias, depender de una respuesta anterior y,
cuando tienen un conjunto cerrado de respuestas, participar de un puntaje
ponderado. El puntaje se calcula al consultar resultados; no se persiste como
un dato independiente.

## Ciclo y segmentación

- Las encuestas pueden ser únicas o recurrentes. El worker ejecuta
  `process_encuestas_rondas` para abrir y cerrar rondas por fecha.
- La segmentación puede ser todos los usuarios o un listado de documentos. Los
  cambios de destinatarios se aplican a la ronda abierta.
- Editar una encuesta con respuestas crea una nueva versión; no se permite
  editarla mientras tenga una ronda abierta.
- Una encuesta obligatoria bloquea la navegación del usuario hasta responder.
  Una no obligatoria permite posponer y programa el próximo aviso.

## Permisos y privacidad

`Gestor de Encuestas` administra encuestas, preguntas, segmentación y rondas.
`Encuestas Resultados` accede al listado y al permiso específico
`encuestas.ver_resultados`, sin adquirir acciones de gestión.

En encuestas anónimas, el sistema conserva el cumplimiento necesario para no
volver a mostrar la ronda, pero resultados y exportaciones no deben asociar el
contenido de una respuesta con una identidad. Los resultados son agregados y
la exportación sigue la política común de CSV/Excel.

## Puntos de entrada

- Dominio y reglas: `encuestas/models.py`, `encuestas/services.py` y
  `encuestas/services_resultados.py`.
- Bloqueo transversal: `encuestas/middleware.py`.
- Operación de rondas: `encuestas/management/commands/process_encuestas_rondas.py`
  y el servicio `encuestas_worker`.
- Diseño y decisiones históricas: `docs/registro/analisis/2026-08-28-modulo-encuestas.md`.
