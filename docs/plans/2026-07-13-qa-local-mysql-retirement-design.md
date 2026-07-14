# Retiro del MySQL local heredado en QA

Estado: Stage 1 aplicado y verificado el 2026-07-13. Observacion hasta
2026-07-20; Stage 2 no aprobado.

## Evidencia

- Django configura `10.80.9.18:3306` y conecta por TCP a `ltestsql-ssies`.
- El MySQL local corre en `mdsldmz-ssies-test` (`10.80.9.15`).
- Ambos reportan el UUID `36dc97f5-e84d-11ee-ab3e-00505681952d`, evidencia de
  un datadir clonado sin regenerar `auto.cnf`, no de una misma instancia.
- El datadir local ocupa 43 GB y contiene multiples schemas historicos/analiticos.
- Antes de Stage 1, MySQL local estaba activo, habilitado y expuesto en
  `0.0.0.0:3306`.

Stage 1 finalizo con cero clientes inesperados, eventos, replicas o miembros de
Group Replication. El servicio quedo inactivo/deshabilitado y sin listener.

## Decision

Separar el retiro en dos etapas.

### Stage 1: reversible

1. Abortar si existe un cliente real conectado, eventos habilitados, replica
   activa o Group Replication.
2. Confirmar que Django sigue conectado a `10.80.9.18`.
3. Crear backup root-only de `/etc/mysql`, `auto.cnf`, paquetes, systemd,
   schemas/tamanios, conexiones y metadatos de replicacion/eventos.
4. Detener y deshabilitar `mysql.service`.
5. Conservar paquetes y `/var/lib/mysql` intactos durante siete dias.
6. Verificar puerto 3306 cerrado, contenedores activos, Django contra la DB
   remota y HTTP 200 en `/` y `/health/`.
7. Ante cualquier fallo, ejecutar rollback automatico con
   `systemctl enable --now mysql`.

### Stage 2: irreversible, no aprobado todavia

Despues de siete dias sin dependencia observada:

- decidir si los datos deben archivarse fuera del host;
- borrar el datadir solo con aprobacion explicita;
- retirar paquetes `mysql-server*`, conservando cliente/librerias requeridos;
- verificar espacio, aplicacion y ausencia del listener.

## Rollback

Mientras el datadir y paquetes se conserven:

```bash
sudo systemctl enable --now mysql
sudo systemctl is-active mysql
sudo ss -lntp 'sport = :3306'
```

No hace falta reiniciar Django para el rollback del servicio local.
