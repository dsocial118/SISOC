# 2026-04-07 - Mobile sync remueve descarte manual temporal

## Cambio

- Se retira del flujo mobile la salida operativa temporal para descartar
  manualmente pendientes `PRESENT_RENDICION` desde la pantalla de
  sincronizacion.

## Alcance

- `mobile/src/features/sync/SyncCenterPage.tsx`

## Motivo

- La accion era provisoria para destrabar pruebas mientras se estabilizaba la
  sincronizacion de rendiciones subsanadas.
- Ahora se prioriza volver al flujo normal sin controles manuales de descarte
  visibles para el usuario.
