# Mobile Nómina alimentaria: dashboard plano y buscador debajo

## Cambio

Se simplifico la cabecera de la pantalla `Nómina alimentaria` para dejarla enfocada en esa vista específica.

## Reglas aplicadas

- Se removieron los filtros/tabs `Consolidada`, `Alimentarias` y `Actividades`.
- La pantalla queda fija sobre la pestaña `alimentaria`.
- El dashboard se mantiene visible.
- Las cards del dashboard pasan a color plano, sin gradiente, respetando la paleta actual de la app.
- El buscador por apellido o DNI se mueve debajo del dashboard.

## Alcance

- Pantalla afectada: `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
- No se cambiaron contratos de API; la vista sigue consultando nómina con `tab=alimentaria`.
