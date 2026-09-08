# Diseño: correcciones de review del módulo Encuestas

## Decisión

Las respuestas de una encuesta anónima no conservan el usuario que las emitió.
`CumplimientoRonda` conserva únicamente el par ronda/usuario para evitar una
segunda respuesta; no referencia a `RespuestaRonda`. Para encuestas no
anónimas, `RespuestaRonda.usuario` continúa disponible para la exportación.

La segmentación `todos_los_usuarios` incluye al creador. El middleware permite
las rutas de gestión a quienes poseen `change_encuesta`, para que el creador no
quede impedido de administrar o cerrar su ronda obligatoria.

## Correcciones adicionales

- Las respuestas de opciones, Sí/No y escala se validan en el servidor.
- Los campos controlados por usuarios se neutralizan antes de exportar CSV/XLSX.
- Pendientes y resultados usan prefetch selectivo para evitar consultas por
  ronda o pregunta.

## Riesgos y validación

Como la migración inicial aún no llegó a un ambiente compartido, se ajusta en
el mismo archivo. Las regresiones cubren anonimato, validación, fórmulas,
permisos de middleware y número de queries.
