# Deploy independiente de satelites y promocion secuencial

Estado: implementado en rama operativa; activacion de GitHub y servidores
pendiente de validacion final.

## Cambio

- SISOC deja de construir o activar Espacios Comunitarios, DataCalle y
  Gestionar durante su propio deploy.
- Cada repositorio satelite despliega `main` en produccion, `homologacion`
  en HML y `development` en QA.
- La promocion descendente ocurre solamente despues de un deploy verificado:
  `main -> homologacion -> development`.
- Produccion conserva el gate manual del GitHub Environment.
- Un run obsoleto no puede promover la punta nueva de una branch.

## Recuperacion

Los satelites restauran la imagen anterior si falla el contenedor o la URL
publica y comprueban el ID restaurado. SISOC restaura el commit anterior,
reconstruye el stack y repite `migrate --check` y el healthcheck.

El rollback de SISOC no revierte migraciones de base de datos. Los cambios de
schema incompatibles requieren la estrategia de migracion/backup especifica de
la release.

## Infraestructura

QA se sirve por HTTP en `10.80.9.15`, solo mediante VPN, sin dominio ni TLS.
Conserva los aliases de produccion: `/mobile/`,
`/pwa/espacioscomunitarios/`, `/pwa/datacalle/`, `/mobile2/`,
`/pwa/gestionar/` y `/mobile3/`.
