# QA - Operaciones

Estado: validado en `qa-old` el 2026-07-13.

## Fuente de verdad

- Host canonico: `qa-old` / `mdsldmz-ssies-test` / `10.80.9.15`.
- Checkout: `/home/admin-ssies/sisoc-comedores-test/BACKOFFICE`.
- Branch: `development`.
- Usuario operativo: `sisoc-deploy`.
- AWS: fuera de alcance; conservar solo como referencia de migracion.
- DB canonica: `10.80.9.18:3306`; el MySQL local es un remanente ya retirado de
  servicio mediante Stage 1.
- MySQL local ocupa 43 GB. Su rol y conexiones fueron clasificados; no borrar
  `/var/lib/mysql` ni purgar paquetes antes del 2026-07-20 y sin aprobar Stage 2.

## Estado rapido

```bash
/home/sisoc-deploy/bin/show_qa_status.sh
/home/sisoc-deploy/bin/healthcheck_qa.sh
systemctl is-active docker containerd nginx cron \
  actions.runner.dsocial118-SISOC.sisoc-qa
systemctl is-active mysql    # esperado durante observacion: inactive
systemctl is-enabled mysql   # esperado durante observacion: disabled
```

El health actual prueba contenedores y HTTP. No demuestra por si solo una consulta
exitosa a la base de datos.

## Disco y mantenimiento Docker

Estado posterior a la limpieza del 2026-07-13:

- `/`: 97 GB totales, 71 GB usados, 22 GB libres, 77%.
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

## MySQL local heredado

Django usa `10.80.9.18`; el MySQL local conserva un datadir clonado de 43 GB.
Stage 1 fue aplicado el 2026-07-13: servicio inactivo/deshabilitado, sin listener,
datadir y paquetes intactos. Observar hasta 2026-07-20.

```bash
bash scripts/infra/retire_qa_local_mysql_stage1.sh
```

Backup root-only:
`/var/backups/sisoc/mysql-local-retirement/20260713_115645`.

Durante la observacion verificar QA, DB remota y que MySQL local no se reactive:

```bash
systemctl is-active mysql || true
systemctl is-enabled mysql || true
ss -lntp 'sport = :3306'
curl --max-time 8 -fsS http://127.0.0.1/health/
```

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
