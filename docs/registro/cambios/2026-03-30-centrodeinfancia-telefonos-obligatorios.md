# Centro de infancia: validación consistente de teléfonos

## Qué cambió

- Se declaró en `CentroDeInfanciaForm` que `telefono` y `telefono_referente` son obligatorios.
- Se unificó el mensaje de error backend para ambos campos con `"Este campo es obligatorio."`.
- Se agregaron tests de regresión para create y update, incluyendo el caso reportado de edición donde se borran ambos teléfonos.

## Problema que resuelve

El módulo de centro de infancia no tenía la obligatoriedad de ambos teléfonos declarada en el contrato del formulario. Eso dejaba el comportamiento dependiente del estado del render/UI y generaba inconsistencia entre alta y edición.

## Impacto esperado

- Alta y edición validan los mismos campos obligatorios.
- Si se intenta guardar sin `telefono` o `telefono_referente`, el formulario vuelve con errores asociados a esos campos.
