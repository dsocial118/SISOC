# Mobile: confirmaciones de baja con modal compartido

Fecha: 2026-03-30

## Qué cambió

- Se reemplazaron las confirmaciones nativas del navegador (`window.confirm`) por un modal visual compartido en SISOC Mobile.
- El patrón quedó unificado para:
  - baja de colaboradores
  - baja de actividades
  - baja de personas en nómina
  - borrado de rendiciones no presentadas

## Implementación

- Se agregó el componente reusable `mobile/src/ui/ConfirmActionModal.tsx`.
- Cada flujo conserva su lógica actual de borrado o baja, pero ahora pide confirmación con la misma UI.
- El modal se presenta centrado en pantalla tanto en mobile como en resoluciones mayores.

## Validación

- `npm run build` en `mobile/`
