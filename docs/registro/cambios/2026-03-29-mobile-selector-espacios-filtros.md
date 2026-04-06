# Mobile selector de espacios con filtros

## Fecha
- 2026-03-29

## Alcance
- Se ajustó el selector de espacios mobile para contemplar programa, organización y proyecto.
- Se extendió el payload de `/api/comedores/` para usuarios PWA con metadata específica del selector.

## Backend
- `GET /api/comedores/` para usuarios PWA ahora devuelve, además de los campos base:
  - `organizacion_id`
  - `organizacion__nombre`
  - `programa_id`
  - `programa__nombre`
  - `codigo_de_proyecto`
  - `localidad__nombre`
  - `tipo_asociacion`
- El listado PWA queda ordenado alfabéticamente por nombre de espacio.
- El flujo no-PWA del endpoint se mantuvo sin cambios.

## Mobile
- La pantalla del selector:
  - detecta si el usuario llega por asociación a organización o por asociación directa a espacios;
  - muestra header distinto según el tipo de vínculo;
  - incorpora filtros por programa, organización y proyecto;
  - muestra provincia y localidad en cada card;
  - mantiene el auto redirect cuando existe un único espacio.
- Si no hay espacios configurados, se muestra un mensaje de bloqueo operativo acorde al requerimiento.

## Validación esperada
- Usuarios con múltiples espacios ven el selector.
- Usuarios con un único espacio siguen ingresando directo al hub.
- Usuarios con asociación por organización pueden refinar por programa, organización y proyecto.
