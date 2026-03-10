# Fix reprocesamiento de registros erróneos sin email/teléfono de responsable

Fecha: 2026-03-10

## Problema

Al editar registros erróneos en el detalle de expediente, el frontend seguía exigiendo `email_responsable` para guardar cambios cuando había responsable.

Eso provocaba que:
- el guardado automático se cortara en cliente (sin feedback claro),
- y luego el reproceso pareciera exigir email aunque backend ya lo trataba como opcional.

## Cambios realizados

- Se ajustó la validación de `static/custom/js/registros_erroneos.js`:
  - responsable requiere solo `apellido_responsable`, `nombre_responsable` y `documento_responsable`.
  - `email_responsable` y `telefono_responsable` no son condición de guardado.
- Se versionó la carga del script en `celiaquia/templates/celiaquia/expediente_detail.html` para forzar recarga de cliente y evitar que quede JS viejo en caché.
- Se agregó test de regresión backend en:
  - `celiaquia/tests/test_reprocesar_registros_erroneos.py`
  - valida que el reproceso funciona con responsable sin email ni teléfono y procesa el registro.

## Impacto

- No cambia permisos ni contratos de endpoints.
- Alinea frontend con la regla de negocio actual: email y teléfono de responsable opcionales.
