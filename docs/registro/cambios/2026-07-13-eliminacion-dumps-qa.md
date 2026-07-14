# 2026-07-13 - Eliminacion de dumps antiguos en QA

## Contexto

Dos dumps SQL no validados ocupaban 7.51 GB en el servidor de aplicacion QA. La
base canonica de QA es remota (`10.80.9.18`), no el MySQL local ni esos archivos.

## Cambios aplicados

Con aprobacion explicita se eliminaron exclusivamente:

- `/home/admin-ssies/dumps/15-07-2025.sql` (2,405,070,758 bytes);
- `/home/admin-ssies/sisoc_local.sql` (5,104,970,363 bytes).

No se usaron comodines ni se tocaron otros archivos, datos MySQL o servicios.

## Impacto esperado

El filesystem raiz bajo de 85% a 77% y el espacio libre subio de 15 GB a 22 GB.

## Validacion

- Ambos paths quedaron ausentes.
- `/` y `/health/` respondieron HTTP 200.
- Docker, containerd, NGINX, MySQL, cron y runner permanecieron activos.
- `10.80.9.18:3306` siguio alcanzable.

## Riesgos y rollback

El borrado fue irreversible y fue autorizado como tal. Los dumps no estaban
validados como backup. La recuperacion de QA debe depender del backup formal de
la DB canonica, que sigue pendiente de auditar.
