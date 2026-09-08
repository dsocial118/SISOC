# Celiaquía: comentarios técnicos y comunicación a Provincia

## Propósito

Los comentarios técnicos estructurados evitan que el equipo de Nación redacte
dos veces el mismo motivo: se registran durante la revisión del legajo y se
usan, cuando corresponde, al solicitar subsanación o rechazarlo.

No existe un modelo paralelo. Se guardan en `HistorialComentarios` con tipo
`COMENTARIO_TECNICO`, preservando legajo, autor, fecha, estado relacionado y
auditoría del historial existente.

## Registro y validación

Cada comentario indica tipo de documento, si tiene observaciones y, en caso
afirmativo, una observación de catálogo o `OTROS` con texto libre. El catálogo
vive en `celiaquia/comentarios_tecnicos.py`; el servicio valida que el código
corresponda al tipo de documento y guarda el texto resuelto como snapshot
histórico. No se sobrescriben comentarios anteriores.

Los comentarios sin observaciones permanecen internos. Las observaciones
repetidas se conservan en el historial interno, pero se deduplican al armar el
motivo que se comunica.

## Publicación y transiciones

Al subsanar o rechazar, el backend recompone el motivo desde las observaciones
positivas, en orden cronológico, más un texto libre opcional. La pantalla sólo
previsualiza ese resultado: no es la fuente de verdad.

La publicación cambia `es_interno` y sella `publicado_en` y `publicado_por`.
Sólo las observaciones positivas se hacen visibles a Provincia; los estados que
pueden mostrar comentarios publicados se enumeran explícitamente para que un
estado nuevo no exponga información interna por accidente.

Se conserva el fallback para legajos históricos que todavía usan motivo libre,
y la compatibilidad con los campos legacy de subsanación. Aprobar no publica ni
exige comentarios.

## Puntos de entrada

- Servicio: `celiaquia/services/comentarios_tecnicos_service/`.
- Catálogo: `celiaquia/comentarios_tecnicos.py`.
- Vistas y permisos de territorio: `celiaquia/views/comentarios.py` y
  `users/territorial_scope.py`.
- Registro de implementación: `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`.
