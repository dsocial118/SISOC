# VAT - retorno al centro al editar ubicaciones adicionales

## Qué cambió

- La actualización de una `Ubicación Adicional` ahora redirige al detalle del centro asociado en lugar de volver a la lista global de ubicaciones.
- El formulario de edición reutiliza la misma URL de retorno para el botón superior de volver y para `Cancelar`.

## Contexto

- En el legajo de centros (`/vat/centros/<pk>/`) las ubicaciones adicionales se gestionan como datos hijos del centro.
- El flujo actual ignoraba esa jerarquía y, al guardar o cancelar una edición, enviaba al usuario a `/vat/institucion/ubicaciones/`, cortando el contexto del legajo.

## Validación esperada

- Entrar al detalle de un centro con ubicaciones adicionales.
- Editar una ubicación existente desde la tabla del legajo.
- Guardar cambios y verificar que la navegación vuelve a `/vat/centros/<pk>/` mostrando los datos actualizados.
