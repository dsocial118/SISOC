# Mobile Hub de espacios: acceso directo a nómina alimentaria

## Cambio

Se agregó un nuevo módulo en el Hub del espacio llamado `Nómina alimentaria`.

## Alcance

- Pantallas afectadas:
  - `mobile/src/features/home/SpaceHubPage.tsx`
  - `mobile/src/features/home/SpaceNominaPage.tsx`
  - `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
  - `mobile/src/app/router.tsx`
- `Nómina` y `Nómina alimentaria` quedan separadas en pantallas distintas para permitir cambios independientes.

## Impacto visible

- El Hub del espacio ahora muestra un acceso nuevo: `Nómina alimentaria`.
- `Nómina` mantiene el comportamiento actual.
- `Nómina alimentaria` abre una pantalla independiente basada en la lógica actual de nómina.
- Se corrigieron textos de interfaz para mantener acentos en UTF-8 y evitar mojibake en cambios recientes.
