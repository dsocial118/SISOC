# Paquete de mantenimiento nocturno de producción

## Estado

Preparado y validado en el repositorio. La primera ventana en `prd-old` aprobo
Gate 0 y se detuvo en Gate 1, con rollback automatico, porque el cambio de
ownership invalido el stat-cache de Git antes de validar el working tree.

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

## Ajuste posterior a Gate 1

- se refresca el indice de Git despues de alinear ownership y antes de ejecutar
  `diff-index`, para no interpretar cambios de metadata como cambios tracked;
- el backup mobile queda sellado con `SHA256SUMS` antes de la primera mutacion,
  de modo que el rollback independiente sea utilizable tambien ante un fallo
  durante el apply;
- una nueva ventana debe reconstruir el paquete desde el nuevo SHA y repetir
  todos los gates; el run productivo anterior no debe aprobarse.
