# 2026-04-09 - Bulk credentials worker en produccion

## Contexto

El worker dedicado de credenciales masivas ya existia en el entrypoint de
Django y en la documentacion del flujo, pero el compose de deploy no lo
declaraba en produccion. Eso dejaba al worker sin arrancar automaticamente al
levantar el stack versionado.

## Cambio aplicado

- Se agrego `docker-compose.produccion.yml` con el servicio
  `bulk_credentials_worker`.
- El servicio usa el mismo build, volumen y usuario que `django`.
- Se define `DJANGO_SERVICE_ROLE=bulk_credentials_worker` para que el
  entrypoint ejecute `manage.py process_bulk_credentials_jobs`.
- Se dejo `restart: unless-stopped` para que el worker vuelva a levantar si
  el proceso termina por error o reinicio del host.

## Decision principal

Se mantuvo el worker fuera del compose local y se activo solo en produccion por
medio del override versionado, para no cambiar el comportamiento de desarrollo
ni de otros entornos que no lo necesiten.

## Validacion esperada

- `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml config -q`
- `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml config`

## Supuesto

Se asume que el deploy de produccion usa el par
`docker-compose.deploy.yml` + `docker-compose.produccion.yml`, tal como
documenta `docs/operacion/instalacion.md`.
