# 2026-06-09 - Celiaquía: subsanación muestra el motivo elegido

## Qué cambió

- Al solicitar una subsanación desde el modal `Subsanar`, ahora se envía el `tipo_subsanacion`
  elegido (RENAPER / Documentación / Datos personales / Otros). Antes el JS armaba el `FormData`
  sólo con `accion` y `motivo`, descartando el tipo, por lo que `subsanacion_tipo` quedaba en
  `None` y el detalle siempre mostraba el texto genérico "Subsanación solicitada".
- El detalle del expediente ahora rotula la respuesta de la provincia según el motivo original
  ("Respuesta a subsanación (Documentación)" …) en lugar del fijo "Respuesta subsanación Renaper".
- El toast de éxito al responder una subsanación ya no dice "Renaper".
- La subsanación originada en la validación RENAPER (`ValidacionRenaperView`) ahora registra
  `subsanacion_tipo="RENAPER"`, para que ese flujo también muestre el motivo y no el genérico.

## Decisión clave

- La causa raíz del estado genérico era el frontend (no se enviaba `tipo_subsanacion`), no el
  backend: `RevisarLegajoView` ya leía y persistía el tipo. El fix es mínimo en JS.
- Para el rótulo de la respuesta se agregaron dos properties (sin migración: sólo lógica de
  presentación): `subsanacion_tipo_display` (traduce el código a etiqueta legible) y
  `subsanacion_respuesta_label` (arma el rótulo completo). El template usa esta última como un
  único `{{ ... }}`, evitando un condicional inline en el HTML. Legajos sin tipo (subsanaciones
  antiguas o creadas por flujos que no lo registran) caen a "Respuesta a subsanación" sin romper.
- No se endureció la validación server-side del tipo para preservar compatibilidad hacia atrás
  (el `<select>` ya es `required` en el cliente y hay un guard adicional en el JS).

## Archivos tocados

- `static/custom/js/expediente_detail.js`
- `celiaquia/models.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/views/respuesta_subsanacion_renaper.py`
- `celiaquia/views/validacion_renaper.py`
- `tests/test_celiaquia_expediente_view_helpers_unit.py`
- `tests/test_validacion_renaper_view_unit.py`
- `celiaquia/tests/test_expediente_detail.py`

## Validación

- `pytest` (SQLite, contenedor one-off) de los tests afectados y el barrido de celiaquía: 158 passed.
- `black --check` limpio sobre los archivos Python tocados.
- `python manage.py makemigrations celiaquia --check --dry-run`: "No changes detected" (las properties no generan migración).
- `pylint --rcfile=.pylintrc`: los archivos tocados no agregan mensajes nuevos (los de `validacion_renaper.py` son preexistentes, en funciones no modificadas).
- `node --check static/custom/js/expediente_detail.js`: OK.
- `djlint --reformat` sobre el template: además de mi cambio, normalizó a multilínea los dos bloques
  `{% if leg.subsanacion_tipo ... %}` de "subsanación solicitada" que ya estaban inline (drift
  preexistente del archivo). Tras el reformateo, los tests siguen pasando.

## Cómo probar manualmente

1. Como técnico/coordinador, evaluar un legajo y elegir Subsanar con tipo "Documentación" y un motivo.
2. En el detalle, el estado debe decir "Subsanación por documentación solicitada" (no el genérico).
3. Como provincia, responder la subsanación: el bloque de respuesta debe rotularse
   "Respuesta a subsanación (Documentación)" y el toast no debe mencionar "Renaper".
