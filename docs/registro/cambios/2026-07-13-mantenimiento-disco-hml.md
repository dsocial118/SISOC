# 2026-07-13 - Mantenimiento conservador de disco en HML

## Contexto

El HML canonico `hml-old` tenia `/` al 93%, con 6.7 GB libres. Docker ocupaba
21 GB y acumulaba 76 imagenes para 3 activas. Media ocupa 48 GB y no se toco.

## Cambios aplicados

- Backup no secreto en
  `/home/jportilla/backups/infra/hml/20260713_132045`.
- Poda de imagenes y build cache sin uso de mas de 14 dias.
- Sin volumenes, contenedores, media, logs, MySQL, restart, deploy o migraciones.
- Scripts operativos instalados bajo `/home/sisoc-deploy/bin`, owner/grupo
  `sisoc-deploy`, modo 750.
- Cron semanal instalado para `sisoc-deploy`, domingo 03:20, con umbral 80%,
  retencion 14 dias y sin volumenes.
- Backup previo a instalacion/crontab:
  `/home/sisoc-deploy/backups/infra/hml/cron-install-20260713_133809`.

## Resultado

- `/`: 93% -> 88%.
- Espacio libre: 6.7 GB -> 12 GB.
- Imagenes Docker: 76 -> 15; las 3 activas permanecieron intactas.
- Contenedores: 3 activos, 0 detenidos.
- Volumenes: 0.

## Validacion

- Checksums y permisos del backup correctos.
- Backend, `/health/`, `/mobile/` y consulta DB remota: OK.
- Docker, containerd, NGINX, MySQL, cron y runner: activos.
- HEAD backend/mobile sin cambios.
- TLS continua invalido por vencimiento previo; no fue modificado.

## Riesgo y rollback

Las imagenes/cache eliminadas no se restauran desde el backup; se reconstruyen
desde el commit registrado. Las imagenes activas no fueron eliminadas. El cron
se revierte restaurando el backup previo; no requiere reiniciar servicios.
