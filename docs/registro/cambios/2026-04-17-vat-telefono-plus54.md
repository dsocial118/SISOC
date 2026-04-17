# VAT teléfonos internacionales en ciudadano

Fecha: 2026-04-17

## Resumen

Se amplió la longitud de `ciudadanos.Ciudadano.telefono` y `telefono_alternativo` a 50 caracteres para
aceptar teléfonos internacionales con prefijo `+54`, separadores e internos sin delegar el rechazo a la base.

## Impacto

- Se agrega una migración que alinea el schema desplegado con el modelo actual.
- El flujo de inscripción web VAT conserva el teléfono internacional del postulante al crear el ciudadano.
- Se documenta el soporte de teléfonos internacionales en la API web VAT.
