# Bases de datos canonicas por entorno

Fuente: definicion operativa confirmada por el responsable el 2026-07-13 y
actualizada con el retiro Stage 2 de QA el 2026-07-21.

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
- Stage 2 retiro los paquetes `mysql-server`, `mysql-server-8.0` y
  `mysql-server-core-8.0`, sin `autoremove`; no queda unidad, binario ni
  listener MySQL local.
- El datadir local `/var/lib/mysql` de 43 GB fue eliminado. El filesystem
  raiz quedo en 34% de uso, con 62 GB libres.
- El preflight final confirmo cero clientes inesperados, eventos, canales de
  replica o miembros de Group Replication. La conexion inicial era interna.
- Se conserva el backup de metadatos de Stage 1 en
  `/var/backups/sisoc/mysql-local-retirement/20260713_115645`; no contiene
  un datadir recuperable y no habilita rollback del MySQL local.
