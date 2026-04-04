# Mobile rendicion: avisos y faltantes en modal

Fecha: 2026-03-31

## Que cambio

- En el detalle de rendicion de SISOC Mobile, los avisos operativos dejaron de mostrarse como bloque inline y ahora se presentan en un modal.
- El cambio cubre especialmente:
  - faltantes de adjuntos obligatorios al intentar `Enviar a revision`,
  - errores al adjuntar o eliminar archivos,
  - avisos de sincronizacion asociados a la rendicion.

## Implementacion

- Se agrego el componente reusable `mobile/src/ui/NoticeModal.tsx`.
- `mobile/src/features/home/SpaceRendicionDetailPage.tsx` ahora separa:
  - error de carga inicial de la pantalla,
  - avisos operativos que deben interrumpir y ser visibles en modal.
- Se mantiene la confirmacion de borrado en `ConfirmActionModal`; el nuevo modal se usa solo para avisos y errores no destructivos.

## Validacion prevista

- `npm run build` en `mobile/`
