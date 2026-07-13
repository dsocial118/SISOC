# Auditoria read-only de infraestructura de produccion

## Cambio

Se documento el entorno canonico `prd-old` en:

- `docs/infra/PROD_INVENTORY.md`;
- `docs/infra/PROD_RISKS.md`;
- `docs/infra/PROD_MIGRATION_CHECKLIST.md`;
- `docs/infra/PROD_CHANGE_PROPOSALS.md`.

## Alcance

La auditoria relevo host, disco, servicios, Docker, repos, paths, DB remota y
local, NGINX/TLS, cron sanitizado, logs, runtimes, dependencias y deploy.

## Restricciones respetadas

- solo lectura en produccion;
- sin ediciones, backups nuevos, stops, reloads, deploys o migraciones;
- sin cambios Git en el checkout remoto;
- sin imprimir secretos, `.env`, queries SQL ni lineas completas de cron/logs;
- AWS fuera de alcance;
- TLS documentado y postergado por decision del responsable.

## Hallazgos principales

- app/DB separadas: Django usa `10.80.5.46`;
- MySQL local heredado activo, 200 MB y sin uso observado;
- siete contenedores activos y health funcional OK;
- 65 GiB de media sin backup/restore demostrado;
- cron root mezcla runtime actual con paths legacy inexistentes;
- logs NGINX fuera de logrotate y access log de ~1.90 GB;
- workflow `main` no incluye deploy mobile, a diferencia de HML;
- disco estable al 12%, sin necesidad de limpieza inmediata.

## Decision

No aplicar cambios en produccion. Las mejoras quedan como propuestas con backup,
rollback, ventana y criterios de exito/fallo para aprobacion futura.
