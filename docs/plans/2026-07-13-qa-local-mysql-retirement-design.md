# Retiro del MySQL local heredado en QA

Estado: Stage 1 aplicado y verificado el 2026-07-13. Tras la observacion y la
aprobacion explicita, Stage 2 fue aplicado el 2026-07-21.

## Evidencia

- Django configura `10.80.9.18:3306` y conecta por TCP a `ltestsql-ssies`.
- El MySQL local corria en `mdsldmz-ssies-test` (`10.80.9.15`).
- Ambos reportan el UUID `36dc97f5-e84d-11ee-ab3e-00505681952d`, evidencia de
  un datadir clonado sin regenerar `auto.cnf`, no de una misma instancia.
- El datadir local ocupaba 43 GB y contenia multiples schemas
  historicos/analiticos.
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

### Stage 2: irreversible, aplicado

Despues de la observacion sin dependencia confirmada, se recibio aprobacion
explicita para eliminar el clon local:

- no se creo un nuevo archivo de los datos historicos; se conserva solo el
  backup de metadatos Stage 1;
- se purgaron `mysql-server`, `mysql-server-8.0` y
  `mysql-server-core-8.0`, sin `autoremove`;
- se elimino `/var/lib/mysql`;
- la unidad, binario y listeners locales quedaron ausentes;
- QA siguio respondiendo HTTP 200 y el filesystem paso de 80% a 34% de uso,
  con 62 GB libres.

## Rollback

El rollback de Stage 1 expiro al aplicar Stage 2: ya no existen los paquetes ni
el datadir requeridos para iniciar el servicio local. No reinstalar MySQL ni
cambiar el routing de Django como sustituto de rollback. La aplicacion continua
con la DB canonica remota `10.80.9.18`; una nueva DB local requeriria una
decision de arquitectura y un plan de datos independiente.
