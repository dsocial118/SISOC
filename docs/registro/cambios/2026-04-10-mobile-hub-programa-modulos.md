# Mobile Hub de espacios: módulos según programa

## Cambio

El Hub del espacio ahora decide qué módulos mostrar según el programa asociado al comedor.

## Reglas aplicadas

- Si el programa contiene `Abordaje Comunitario`, se muestran:
  - `Nómina`
  - `Actividades`
- Si el programa contiene `Alimentar Comunidad`, se muestra:
  - `Nómina alimentaria`
- Si no hay programa definido, se muestra la leyenda:
  - `No hay programa definido. Comuníquese con un administrador de la aplicación.`

## Alcance

- Pantalla afectada: `mobile/src/features/home/SpaceHubPage.tsx`
- La resolución se hace con el nombre del programa informado por el detalle del espacio.
