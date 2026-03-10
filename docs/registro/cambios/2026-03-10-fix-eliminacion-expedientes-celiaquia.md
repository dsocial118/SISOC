# Fix eliminación de expedientes en Celiaquía

Fecha: 2026-03-10

## Contexto

En la bandeja de expedientes (`/celiaquia/expedientes/`) el botón **Eliminar** podía no ejecutar acción cuando el binding del evento quedaba asociado a un contenedor de tabla distinto al que contenía el botón.

## Cambios realizados

- Se ajustó `attachDeleteExpedienteHandlers()` en `static/custom/js/celiaquia_list.js` para delegar el click en `document` y capturar de forma robusta `.js-delete-expediente`.
- Se ajustó `ExpedienteDeleteView` para devolver JSON `404` cuando el expediente no existe/ya fue eliminado (evita volcar HTML de debug en la UI).
- Se mejoró el manejo de error en frontend para `404` con mensaje corto y claro.
- Se agregaron tests de regresión del endpoint de eliminación en `celiaquia/tests/test_expediente_delete.py`:
  - superusuario puede eliminar expediente.
  - usuario no superusuario recibe `403`.
  - expediente inexistente responde `404` en JSON.

## Impacto

- No cambia contrato del endpoint ni permisos.
- Mejora robustez del handler frontend ante cambios de estructura/render de tabla.
