# Cambio: trabajadores en Centro de Infancia

## Fecha
- 2026-03-17

## Resumen
- Se agregó el modelo `Trabajador` asociado a `CentroDeInfancia`.
- Se incorporó una nueva sección `Trabajadores` en el acordeón del detalle del centro.
- Desde esa sección ahora se puede agregar, editar y eliminar trabajadores sin salir de la página.

## Comportamiento
- Alta y edición se resuelven con un modal Bootstrap reutilizable.
- La baja se confirma con un modal específico antes de enviar el POST.
- `telefono` queda opcional.
- El `rol` usa opciones cerradas: `Profesor`, `Director`, `Administrativo`.

## Permisos aplicados
- La sección se muestra a quien ya puede ver el detalle del centro.
- Alta y edición reutilizan `change_centrodeinfancia`.
- Eliminación reutiliza `delete_centrodeinfancia`.

## Validación
- Se agregaron tests del detalle, alta, edición, baja lógica, scope por provincia y reverse de rutas.
