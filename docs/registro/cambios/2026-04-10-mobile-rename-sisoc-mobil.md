# Mobile: rename de Mi Espacio a SiSOC Mobil

## Cambio

Se actualizó el nombre visible de la app mobile de `Mi Espacio` a `SiSOC Mobil`.

## Alcance

- Branding y metadatos de PWA:
  - `mobile/index.html`
  - `mobile/vite.config.ts`
  - `mobile/src/pwa/InstallPwaModal.tsx`
  - `mobile/src/sw.ts`
- Metadata del paquete:
  - `mobile/package.json`
  - `mobile/package-lock.json`
- Documentación local:
  - `mobile/README.md`

## Impacto visible

- La pestaña del navegador y el nombre instalado de la PWA pasan a mostrarse como `SiSOC Mobil`.
- El modal de instalación también usa el nuevo nombre.
