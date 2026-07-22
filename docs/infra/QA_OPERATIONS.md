# QA - Operaciones

Estado: actualizado en `qa-old` el 2026-07-21, despues del retiro Stage 2
del MySQL local.

## Fuente de verdad

- Host canonico: `qa-old` / `mdsldmz-ssies-test` / `10.80.9.15`.
- Checkout: `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE`.
- Branch: `development`.
- Usuario operativo: `sisoc-deploy`.
- AWS: fuera de alcance; conservar solo como referencia de migracion.
- DB canonica: `10.80.9.18:3306`; no hay MySQL server local en el host de
  aplicacion.
- Stage 2 elimino el datadir heredado de 43 GB y los paquetes server locales.
  No existe rollback local; la DB canonica remota no fue modificada.

## Estado rapido

```bash
/home/sisoc-deploy/bin/show_qa_status.sh
/home/sisoc-deploy/bin/healthcheck_qa.sh
systemctl is-active docker containerd nginx cron \
  actions.runner.dsocial118-SISOC.sisoc-qa
systemctl show mysql -p LoadState --value || true # esperado: not-found
command -v mysqld || true                         # esperado: sin salida
ss -lntp 'sport = :3306'                           # esperado: sin listener
```

El health actual prueba contenedores y HTTP. No demuestra por si solo una consulta
exitosa a la base de datos.

## Disco y mantenimiento Docker

Estado observado despues del retiro Stage 2 el 2026-07-21:

- `/`: 97 GB totales, 31 GB usados, 62 GB libres, 34%.
- imagenes: 2, ambas activas;
- volumenes Docker: 0;
- build cache restante: 1.79 GB, preservado por la retencion.
- dumps SQL antiguos detectados: eliminados con aprobacion el 2026-07-13;
  recuperaron aproximadamente 7.51 GB adicionales.

Vista previa, sin cambios:

```bash
/home/sisoc-deploy/bin/cleanup_qa_disk.sh
```

Ejecucion manual aprobada:

```bash
/home/sisoc-deploy/bin/cleanup_qa_disk.sh --apply --yes
```

La tarea solo actua cuando `/` esta al 80% o mas. Conserva 14 dias, valida host y
`ENVIRONMENT=qa`, usa lock y nunca poda volumenes. Registra eventos con tag
`sisoc-qa-disk-cleanup`:

```bash
journalctl -t sisoc-qa-disk-cleanup --since today --no-pager
```

Cron instalado para `sisoc-deploy`:

```cron
0 3 * * 0 /home/sisoc-deploy/bin/cleanup_qa_disk.sh --apply --yes >/dev/null 2>&1
```

## Backup de configuracion

```bash
/home/sisoc-deploy/bin/backup_qa_configs.sh
```

El backup queda fuera del repo bajo
`/home/sisoc-deploy/backups/infra/qa/YYYYMMDD_HHMMSS/`, con directorios 700,
archivos 600 y `SHA256SUMS`. De `.env` guarda solo nombres de variables.

Backup previo a la primera limpieza:

`/home/sisoc-deploy/backups/infra/qa/20260713_110704`

Snapshot posterior con cron y scripts instalados:

`/home/sisoc-deploy/backups/infra/qa/20260713_111618`

## Logs

- Django: `$APP_ROOT/logs/`.
- NGINX: `/var/log/nginx/staging-sisoc-access.log` y
  `/var/log/nginx/staging-sisoc-error.log`.
- Mantenimiento de disco: journal tag `sisoc-qa-disk-cleanup`.
- Runner: `journalctl -u actions.runner.dsocial118-SISOC.sisoc-qa`.

No pegar logs completos en tickets o chats: pueden contener PII, URLs o datos
operativos.

## MySQL local heredado retirado

Django usa `10.80.9.18`. Stage 1 dejo el MySQL local inactivo/deshabilitado
el 2026-07-13; tras la observacion aprobada, Stage 2 del 2026-07-21 purgo
`mysql-server`, `mysql-server-8.0` y `mysql-server-core-8.0` sin
`autoremove`, y elimino `/var/lib/mysql`.

No queda unidad `mysql.service`, binario `mysqld`, listener local ni
datadir. El backup root-only
`/var/backups/sisoc/mysql-local-retirement/20260713_115645` se conserva
solo como evidencia de Stage 1; no permite reactivar ni recuperar el clon
local.

No ejecutar `retire_qa_local_mysql_stage1.sh` nuevamente: presupone un
servicio y datadir que ya no existen. Si alguna vez se evaluara una nueva DB
local, debe ser una decision de arquitectura separada, no un rollback.

## Restart y deploy

No hay un restart inocuo: el entrypoint ejecuta migraciones, fixtures,
`create_test_users`, grupos y `collectstatic`. Los scripts versionables exigen
`--apply --acknowledge-db-writes`, pero no deben ejecutarse sin una aprobacion
especifica:

```bash
bash scripts/infra/restart_qa.sh
bash scripts/infra/deploy_qa.sh
```

Sin flags solo muestran el plan y no hacen cambios.
