# HML - Operaciones

Estado: validado en `hml-old` el 2026-07-13.

## Fuente de verdad

- Host: `hml-old` / `ldmzssies-homolo` / `10.80.5.47`.
- Backend: `/sisoc/SISOC`, branch `homologacion`.
- Mobile: `/sisoc/SISOC-Mobile`, branch `main`.
- DB: `10.80.5.48:3306`, schema `sisoc_local`.
- Dominio: `hml-sisoc.secretarianaf.gob.ar`.
- AWS: fuera de alcance; solo referencia de migracion.

## Estado rapido

Las fuentes versionables estan en `scripts/infra/` y las copias operativas en
`/home/sisoc-deploy/bin/`:

```bash
/home/sisoc-deploy/bin/show_hml_status.sh
/home/sisoc-deploy/bin/healthcheck_hml.sh
/home/sisoc-deploy/bin/cleanup_hml_disk.sh
```

Sin flags la limpieza solo muestra estado/plan. El health funcional usa la DB
remota y verifica backend/mobile. Informa por separado que TLS esta vencido.

## Disco y Docker

Resultado de la limpieza manual aprobada:

- `/`: 93% -> 88%; 6.7 GB -> 12 GB libres.
- imagenes: 76 -> 15; 3 activas intactas.
- contenedores: 3 activos, 0 detenidos.
- volumenes: 0.
- build cache restante protegido por retencion de 14 dias.

La ejecucion real requiere aprobacion:

```bash
/home/sisoc-deploy/bin/cleanup_hml_disk.sh --apply --yes
```

Cron instalado para `sisoc-deploy`:

```cron
20 3 * * 0 /home/sisoc-deploy/bin/cleanup_hml_disk.sh --apply --yes >/dev/null 2>&1
```

Backup del estado anterior e instalacion:

`/home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809`

Eventos de una ejecucion aplicada:

```bash
journalctl -t sisoc-hml-disk-cleanup --since today --no-pager
```

## Backup de configuracion

Backup validado:

`/home/jportilla/backups/infra/hml/20260713_132045`

Contiene inventario Docker, Git, NGINX, systemd, Compose, metadata TLS y solo
nombres de variables. No contiene valores `.env` ni la clave privada TLS.

## Servicios y health

```bash
systemctl is-active docker containerd nginx mysql cron \
  actions.runner.dsocial118-SISOC.sisoc-homologacion
docker ps
curl --max-time 8 -kfsS https://hml-sisoc.secretarianaf.gob.ar/health/
curl --max-time 8 -kfsS https://hml-sisoc.secretarianaf.gob.ar/mobile/
```

`-k` solo permite verificar funcionalidad mientras el certificado esta vencido.
No usarlo para declarar TLS valido.

## Pendientes operativos

1. Obtener el wildcard Sectigo renovado desde Infra y corregir TLS mediante un
   cambio con backup, `nginx -t` y rollback. Certbot no administra el actual.
2. Monitorear la primera ejecucion automatica del mantenimiento semanal.
3. Definir backup y crecimiento de los 48 GiB de media.
4. Observar hasta al menos el 2026-07-20 el Stage 1 del MySQL local; no purgar
   datadir ni paquetes sin aprobacion separada.
5. Probar el deploy/rollback de SISOC-Mobile en una ventana aprobada; el flujo
   vigente ya esta documentado en `HML_DEPLOY.md`.

## MySQL local retirado - Stage 1

Estado verificado el 2026-07-13:

```text
ActiveState=inactive
UnitFileState=disabled
listener local 3306=ausente
Django DB=10.80.5.48/ldmzsql-homolo/sisoc_local
health funcional=OK
```

Backup root-only:

`/var/backups/sisoc/mysql-local-retirement/hml/20260713_135622`

El datadir y los paquetes siguen intactos. Ver rollback y criterio de observacion
en `HML_ROLLBACK.md`. El script versionado es
`scripts/infra/retire_hml_local_mysql_stage1.sh`.
