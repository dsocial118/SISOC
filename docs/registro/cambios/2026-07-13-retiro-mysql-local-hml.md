# Retiro reversible del MySQL local de HML

## Cambio

El 2026-07-13 se detuvo y deshabilito `mysql.service` en `hml-old`. No se
eliminaron paquetes, configuracion ni `/var/lib/mysql`.

## Decision

La aplicacion usa la DB separada `10.80.5.48`. El MySQL local tenia 200 MB, cero
schemas de aplicacion, clientes, eventos y replicacion. Se eligio un Stage 1
reversible para reducir superficie y ruido sin asumir que ya puede purgarse.

## Backup y rollback

Backup root-only:

`/var/backups/sisoc/mysql-local-retirement/hml/20260713_135622`

Rollback aprobado: `sudo systemctl enable --now mysql`, seguido por validacion de
listener y confirmacion de que Django permanece conectado a `10.80.5.48`.

## Validacion

- `mysql.service`: inactivo y deshabilitado;
- listener local 3306: ausente;
- Django: `10.80.5.48`, servidor `ldmzsql-homolo`, schema `sisoc_local`;
- contenedores Django, OCR y mobile: activos;
- health funcional HML: OK;
- disco: 88%, 12 GB libres;
- checkout `/sisoc/SISOC`: limpio en `homologacion`.

## Riesgos pendientes

No purgar datadir/paquetes antes del 2026-07-20 ni sin aprobacion separada. El
certificado TLS vencido es preexistente y quedo fuera de este cambio.
