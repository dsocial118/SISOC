# Bases de datos canonicas por entorno

Fuente: definicion operativa confirmada por el responsable el 2026-07-13.

## Politica

Los servidores de aplicacion no deben alojar MySQL local. Cada entorno consume un
host de base separado:

| Entorno | Servidor de aplicacion canonico | Host MySQL canonico |
| --- | --- | --- |
| QA | `qa-old` (`10.80.9.15`) | `10.80.9.18` |
| HML | `hml-old` (`10.80.5.47`) | `10.80.5.48` |
| PRD | `prd-old` (`10.80.5.45`) | `10.80.5.46` |

Los aliases AWS quedan fuera de alcance y solo representan una posible migracion
futura. No son canonicos actualmente.

## Consecuencias operativas

- No instalar ni conservar MySQL server en los hosts de aplicacion.
- Mantener solo el cliente/librerias que requieran la aplicacion o los scripts.
- Antes de retirar una instancia local heredada, confirmar routing, conexiones,
  cron/systemd, datos, backup y rollback.
- No copiar dumps locales antiguos como fuente de verdad de una migracion.
- Tratar los hosts DB como infraestructura independiente, con backup, restore,
  capacidad, ACL y monitoreo propios.

## Estado QA observado

- `.env` de QA apunta a `10.80.9.18:3306`, schema `sisoc_local`.
- `10.80.9.18:3306` es alcanzable desde `qa-old`.
- MySQL local en `qa-old` quedo inactivo y deshabilitado en Stage 1; no hay
  proceso ni listener 3306 local.
- `/var/lib/mysql` ocupa 43 GB y contiene multiples schemas historicos/analiticos;
  los mayores son `dw_PA` (~17.8 GB), `sisoc_local` (~6.9 GB),
  `SISOC_Comedores` (~4.2 GB), `DW_DD` (~2.0 GB) y `DW_HSU` (~1.4 GB).
- El preflight final confirmo cero clientes inesperados, eventos, canales de
  replica o miembros de Group Replication. La conexion inicial era interna.
- `/var/lib/mysql` y paquetes quedan intactos hasta 2026-07-20 para rollback.
- Backup de Stage 1:
  `/var/backups/sisoc/mysql-local-retirement/20260713_115645`.
