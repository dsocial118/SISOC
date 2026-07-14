# 2026-07-13 - Mantenimiento conservador de disco en QA

## Contexto

El QA canonico `qa-old` tenia el filesystem raiz al 93%, con 7.2 GB libres.
Docker acumulaba imagenes y build cache porque el crontab efectivo de
`sisoc-deploy` estaba vacio. El contrato historico `scripts/crontab` apuntaba a
paths inexistentes y proponia `docker system prune --volumes`.

## Cambios aplicados

- Backup de configuracion e inventario fuera del repo en
  `/home/sisoc-deploy/backups/infra/qa/20260713_110704`.
- Snapshot posterior reproducible, con cron y scripts instalados, en
  `/home/sisoc-deploy/backups/infra/qa/20260713_111618`.
- Poda de imagenes y build cache sin uso con mas de 14 dias.
- Scripts operativos instalados bajo `/home/sisoc-deploy/bin/`.
- Cron semanal de `sisoc-deploy`, domingo 03:00, condicionado por uso de `/`
  igual o mayor a 80%.
- `.dockerignore`, scripts versionables y documentacion operativa preparados en
  el repo local; no se hizo commit ni push.

No se tocaron volumenes, contenedores, dumps, media, MySQL, NGINX, `.env`,
permisos existentes ni servicios. No hubo restart, deploy ni migraciones.

## Impacto esperado

- Uso de `/` reducido de 93% a 85%; espacio libre de 7.2 GB a 15 GB.
- Menor riesgo de que despliegues sucesivos acumulen capas indefinidamente.
- Builds futuros pueden tardar mas cuando una capa podada deba reconstruirse.

## Validacion

- Checksums y permisos del backup verificados.
- Scripts validados con `bash -n` en el host QA.
- Mismos contenedores e IDs de imagen antes/despues.
- Docker, containerd, NGINX, MySQL, cron y runner activos.
- `/` y `/health/` respondieron HTTP 200.
- Guard de umbral probado con un umbral superior al uso actual.
- Crontab verificado con una sola entrada de mantenimiento.

## Riesgos y rollback

Las imagenes/cache podadas no tienen restauracion binaria; una version antigua se
reconstruye desde Git. Se preservaron 14 dias y el inventario previo. El cron se
revierte restaurando
`status/crontab.sisoc-deploy.txt` desde el backup. No es necesario reiniciar
Docker para deshabilitar la tarea.
