# 2026-07-21 - Retiro Stage 2 del MySQL local de QA

## Contexto

El MySQL local heredado de `qa-old` (`mdsldmz-ssies-test`) ya llevaba la
ventana de observacion de Stage 1 sin dependencias confirmadas. Django usa la
DB canonica remota `10.80.9.18` (`ltestsql-ssies`), no el clon local de
43 GB.

## Cambios aplicados

- Con aprobacion explicita se purgaron solamente `mysql-server`,
  `mysql-server-8.0` y `mysql-server-core-8.0`.
- No se ejecuto `autoremove`, por lo que no se solicito retirar cliente ni
  librerias MySQL.
- Se elimino `/var/lib/mysql`.
- Se conserva
  `/var/backups/sisoc/mysql-local-retirement/20260713_115645` como evidencia
  de Stage 1; contiene metadatos, no una copia recuperable del datadir.

## Validacion

- El guard de Stage 2 verifico que Django seguia conectado a
  `10.80.9.18|ltestsql-ssies|sisoc_local` antes y despues de la purga.
- No se reinicio ni redesplego la aplicacion.
- La inspeccion posterior por SSH confirmo unidad MySQL `not-found`, ausencia
  de binario, paquetes, listeners 3306/33060 y `/var/lib/mysql`.
- QA respondio HTTP 200 en `/health/`.
- El filesystem raiz paso de 80% a 34% de uso, con 62 GB libres.

## Riesgos y seguimiento

El retiro es irreversible para el clon historico local. No reinstalar MySQL
local ni usar el backup de Stage 1 como supuesto rollback. Sigue pendiente
obtener evidencia de backup, retencion y restore probado de la DB canonica
remota.
