# Mobile: volver atrás sin recarga global del layout

Fecha: 2026-03-30

## Qué cambió

- La app mobile deja de mostrar la carga global del layout en cada cambio de ruta.
- Al volver hacia atrás ya no se fuerza una sensación de recarga completa de toda la app.

## Implementación

- En `AppLayout` se eliminó el `key={location.pathname}` que forzaba remontar el contenedor principal en cada navegación.
- El overlay global de skeleton y spinner deja de depender de cada cambio de `pathname` y ahora sólo aparece cuando una pantalla lo solicita explícitamente mediante `PageLoadingContext`.

## Validación

- `npm run build` en `mobile/`
