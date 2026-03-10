# Fix eliminación de expedientes en Celiaquía

Fecha: 2026-03-10

## Contexto

En la bandeja de expedientes (`/celiaquia/expedientes/`) el botón **Eliminar** podía no ejecutar acción cuando el binding del evento quedaba asociado a un contenedor de tabla distinto al que contenía el botón.

## Cambios realizados

- Se ajustó `attachDeleteExpedienteHandlers()` en `static/custom/js/celiaquia_list.js` para delegar el click en `document` y capturar de forma robusta `.js-delete-expediente`.
- Se habilitó soft delete en `Expediente`:
  - `Expediente` ahora hereda de `SoftDeleteModelMixin`.
  - migración `0010_expediente_soft_delete_fields.py` agrega `deleted_at` y `deleted_by`.
- Se ajustó `ExpedienteDeleteView` a comportamiento idempotente: si el expediente no existe/ya fue eliminado, responde `200` con `success=true` y `already_deleted=true`.
- Se mejoró el manejo de error en frontend para `404` con mensaje corto y claro.
- Se agregaron tests de regresión del endpoint de eliminación en `celiaquia/tests/test_expediente_delete.py`:
  - superusuario puede eliminar expediente.
  - usuario no superusuario recibe `403`.
  - expediente inexistente responde éxito idempotente (`200`, `already_deleted=true`).
  - eliminación de superusuario deja el expediente fuera del manager por defecto y con `deleted_at` informado en `all_objects`.

## Impacto

- No cambia contrato del endpoint ni permisos.
- La eliminación de expedientes pasa a ser baja lógica (ya no borrado físico directo).
- Mejora robustez del handler frontend ante cambios de estructura/render de tabla.
