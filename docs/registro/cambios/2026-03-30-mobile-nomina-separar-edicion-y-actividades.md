# Mobile nómina: separar edición personal y actividades

## Fecha
- 2026-03-30

## Cambio
- En el detalle de persona de nómina se agregó un botón específico para vincular actividades.
- El botón `Editar` pasó a `Editar datos`.
- La edición personal y la gestión de actividades dejaron de compartir la misma pantalla operativa.

## Mobile
- Nueva ruta: `/app-org/espacios/:spaceId/nomina/:nominaId/actividades`
- Desde el detalle de persona:
  - `Editar datos` abre la edición personal
  - `Sumar a actividad` abre la gestión de actividades vinculadas
- La pantalla de edición personal ya no muestra el bloque de actividades.
- La pantalla de actividades reutiliza el formulario de nómina en un modo dedicado.

## Nota funcional
- Para personas documentadas, Mobile no permite modificar datos personales; se muestra un mensaje para regularizar en SISOC Web.

## Validación
- `npm run build` en `mobile/`
