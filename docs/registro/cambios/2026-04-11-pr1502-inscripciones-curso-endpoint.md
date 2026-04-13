## Cambio

Se restringió `POST /api/vat/inscripciones-curso/` para aceptar únicamente `comision_curso`.

## Motivo

El endpoint explícito de comisiones de curso heredaba la creación genérica de inscripciones y todavía permitía crear altas sobre `Comision` legacy. Eso dejaba el recurso inconsistente porque su propio `GET` solo lista inscripciones con `comision_curso`.

## Impacto

- El recurso ahora rechaza con `400` payloads que intenten usar `comision`.
- No se modificó el contrato general de `/api/vat/inscripciones/`.
