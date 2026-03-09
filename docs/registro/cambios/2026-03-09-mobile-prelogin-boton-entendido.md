## Cambio

Se ajusto el boton `Entendido` del modal de instalacion PWA que aparece en el prelogin de Mobile.

## Motivo

El ancho fijo del componente `SmallWhiteButton` quedaba corto para ese texto y hacia que el boton se viera desbalanceado en esa pantalla.

## Implementacion

- Se mantuvo el componente reutilizable existente.
- Se aplico un override local en `mobile/src/pwa/InstallPwaModal.tsx` para dar mas ancho util, padding horizontal y una altura levemente mayor solo en ese modal.

## Impacto

- Mejora visual del CTA `Entendido` en prelogin.
- Sin cambios funcionales ni de comportamiento en otros botones de Mobile.
