# Paquete de mantenimiento nocturno de producción

## Estado

Preparado y validado en el repositorio. No ejecutado en `prd-old`.

## Alcance

- preflight read-only con barreras de host, disco, Git, Docker, DB y health;
- backup root-only de configuracion y metadata sin publicar secretos;
- alineacion reversible del checkout mobile con el usuario del runner, con
  backup completo de owners/ACL y normalizacion del origin publico a HTTPS;
- reemplazo controlado de la poda root con `--volumes` por mantenimiento diario
  como `sisoc-deploy`, umbral 80% y retencion de 14 dias;
- logrotate dedicado para NGINX bajo `/sisoc`;
- hardening de permisos del `.env` mobile;
- disable reversible de dos servicios legacy inactivos;
- Stage 1 del MySQL local con backup y rollback automatico;
- verificacion por SHA de backend/mobile y del runtime final;
- rollback host-side desde el backup creado por la instalacion.

## Seguridad

Los scripts no borran media, backups, checkouts, datadir MySQL, paquetes ni
volumenes Docker. No imprimen `.env` ni variables de contenedores. TLS queda
fuera del alcance.

## Validacion

- `bash -n` sobre los diez scripts productivos;
- pruebas focalizadas de invariantes destructivos: cleanup sin system/volume
  prune, Stage 1 sin purge/`rm -rf`/DROP y cron de cleanup sin privilegios root;
- `git diff --check`.

La validacion real de host requiere el preflight nocturno y un GO explicito.
