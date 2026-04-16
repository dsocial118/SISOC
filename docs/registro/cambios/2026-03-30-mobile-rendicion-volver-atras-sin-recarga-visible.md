# Mobile: volver atrás en rendiciones sin recarga visible

Fecha: 2026-03-30

## Qué cambió

- Al volver atrás dentro del flujo de rendiciones, el selector y el listado reutilizan los datos ya cargados en la sesión.
- Esto evita que esas pantallas vuelvan a mostrarse vacías o en carga completa cada vez que el usuario regresa desde una rendición.

## Implementación

- Se agregó un cache en memoria para el hub de rendiciones y para el listado por espacio.
- Las pantallas se hidratan primero desde ese cache y después refrescan en segundo plano contra la fuente offline-first existente.
- El loading visible sólo se muestra cuando todavía no hay datos previos para reutilizar.

## Validación

- `npm run build` en `mobile/`
