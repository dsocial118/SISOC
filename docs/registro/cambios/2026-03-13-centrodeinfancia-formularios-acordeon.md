# Cambio: mover Formularios al acordeón del detalle CDI

Fecha: 2026-03-13

## Qué cambia
- La sección `Formularios` del detalle de `Centro de Infancia` deja de renderizarse como card independiente.
- Pasa a mostrarse como un panel más dentro del acordeón horizontal existente.
- El header vertical del panel `Formularios` usa un color propio para mantener consistencia visual con el resto de secciones del acordeón.

## Alcance
- Se mantiene el mismo contenido del resumen:
  - últimas 3 instancias
  - acciones `Ver todos`
  - acción `Nuevo formulario` según permisos
- No se modifican permisos ni la obtención de datos del backend.

## Validación prevista
- Test del detalle CDI verificando que la sección de formularios sigue visible para usuarios con permiso y ahora usa el header del acordeón.
