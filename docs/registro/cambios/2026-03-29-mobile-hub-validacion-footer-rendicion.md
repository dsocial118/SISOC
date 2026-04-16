# Mobile Hub: validación operativa y acceso a rendición en footer

## Fecha
- 2026-03-29

## Alcance
- Ajuste del Hub mobile para alinear validaciones de acceso operativo y presentación de módulos.

## Cambios
- Se corrigió la validación del Hub para no depender solo del detalle del espacio.
- El Hub ahora verifica si el espacio actual sigue estando dentro de los espacios accesibles del usuario.
- Si no hay asociación operativa válida, se bloquea el acceso con un mensaje de regularización en SISOC Web.
- Se mantuvieron como módulos centrales:
  - Información Institucional
  - Mensajes
  - Actividades
  - Nómina
- `Rendición de Cuentas` quedó como acceso separado en el footer del Hub.

## Notas
- La validación de sesión activa continúa resuelta por `ProtectedRoute`.
- La validación del espacio antes de operar continúa apoyada en `getSpaceDetail(...)`.
