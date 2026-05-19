# Setup PRD Docker, NGINX y MySQL

Fecha: 2026-05-19

## Contexto

Se preparo el entorno productivo de SISOC con el patron simple validado en HML: Docker Compose para la app, MySQL 8.0 en host separado, NGINX como reverse proxy y firewall minimo. La branch desplegada fue `main` y el perfil Django quedo como `ENVIRONMENT=prd`.

El dominio publico `sisoc.secretarianaf.gob.ar` no fue reapuntado todavia al nuevo SITE-PRD. Por decision operativa, no se implemento TLS en este paso; queda pendiente para el corte de DNS.

## Rutas y hosts

| Componente | Valor |
| --- | --- |
| SITE-PRD | `10.1.135.170` |
| DB-PRD | `10.1.138.80` |
| Repo SITE | `/opt/sisoc/SISOC` |
| MySQL operativo | `/opt/sisoc-mysql` |
| Compose MySQL | `/opt/sisoc-mysql/compose.yml` |
| DB Django | `sisoc_prd` |
| Usuario app DB | `djangoapp` |

## Cambios aplicados

- Se valido que `origin/main` contiene `origin/development` y que el commit desplegado fue `c67bf57f`.
- Se preparo `/opt/sisoc-mysql` con MySQL `mysql:8.0`.
- Se corrigieron permisos operativos: `.env` de MySQL `0600` e `init/01-users.sql` legible para el usuario MySQL del contenedor.
- Se restauro el dump indicado por operacion desde `sisoc_local.sql.gz` hacia la base `sisoc_prd`.
- Se creo backup preventivo antes de restaurar: `/opt/sisoc-mysql/backups/sisoc_prd_pre_restore_20260519_151809.sql.gz`.
- Se valido `djangoapp@'%'` con permisos para la aplicacion, incluyendo `REFERENCES`, sin usar root para Django.
- Se bloqueo `root@'%'`.
- Se creo/uso el usuario Linux `sisoc-deploy` y se clono el repo en `/opt/sisoc/SISOC`.
- Se dejo `.env` productivo con `ENVIRONMENT=prd`, `DJANGO_DEBUG=False`, `WAIT_FOR_DB=true`, `RUN_MAKEMIGRATIONS_ON_START=false` y DB remota en `10.1.138.80`.
- Se levanto la app con:

```bash
docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml up -d --build
```

- Se confirmo que el override productivo levanta `django`, `bulk_credentials_worker` y `ciudadanos_import_worker`.
- Se configuro NGINX HTTP-only hacia `http://127.0.0.1:8001`, con `/static/` y `/media/` desde el repo operativo.
- Se agrego preservacion de `X-Forwarded-Proto` para validar el perfil `prd` antes del TLS real.

## Decisiones y diferencias contra el runbook base

- No se implemento TLS porque el dominio sera reapuntado mas adelante. Por lo tanto, tampoco se abrio `443/tcp` en SITE-PRD.
- No se agregaron overrides inseguros de HML en PRD. En particular, no se setearon `DJANGO_SECURE_SSL_REDIRECT=False`, `DJANGO_SESSION_COOKIE_SECURE=False`, `DJANGO_CSRF_COOKIE_SECURE=False` ni `DJANGO_SECURE_HSTS_SECONDS=0`.
- Como `SECURE_SSL_REDIRECT` queda activo por `ENVIRONMENT=prd`, el health por HTTP plano directo puede responder `301`. La validacion pre-corte debe enviar `X-Forwarded-Proto: https`.
- El compose productivo de `origin/main` incluye `ciudadanos_import_worker` ademas de `bulk_credentials_worker`; ambos deben revisarse en deploy PRD.
- El datadir MySQL ya existia antes del setup. Root no autenticaba con el `.env` nuevo y se reseteo sin borrar datos, usando modo local con `--skip-grant-tables --skip-networking`.
- En DB-PRD quedo una regla previa de firewall para `10.1.14.181` pendiente de confirmar como VPN. No se abrio MySQL global.

## Validaciones realizadas

- SSH a SITE-PRD y DB-PRD.
- `docker ps`, `docker compose ls`, servicios Docker/NGINX/MySQL y UFW en ambos hosts.
- MySQL 8.0 activo y `djangoapp` conectando localmente contra `sisoc_prd`.
- `djangoapp` ve `django_migrations`.
- `root@'%'` bloqueado.
- App levantada con `docker-compose.deploy.yml` + `docker-compose.produccion.yml`.
- Logs de `django`, `bulk_credentials_worker` y `ciudadanos_import_worker` sin tracebacks detectados.
- NGINX con `nginx -t` exitoso y reverse proxy a `127.0.0.1:8001`.
- `/health/` con header `X-Forwarded-Proto: https` devuelve `200 OK` por NGINX local y por `curl --resolve` al SITE-PRD.
- El dominio publico aun resuelve a la publicacion anterior, no al SITE-PRD nuevo.

## Estado pendiente

- Reapuntar `sisoc.secretarianaf.gob.ar` al SITE-PRD.
- Emitir e instalar certificado TLS real.
- Habilitar `443/tcp` en SITE-PRD una vez instalado TLS.
- Confirmar si `10.1.14.181` corresponde a VPN; si no corresponde, retirar esa regla de DB-PRD.
- Validar health final por `https://sisoc.secretarianaf.gob.ar/health/` despues del corte.

## Actualizacion temporal: acceso HTTP por navegador

Despues del setup inicial, operacion pidio que el entorno pueda abrirse desde navegador antes de tener dominio apuntado y certificado TLS. Para eso se habilito una excepcion temporal de HTTP directo en SITE-PRD.

Backup previo del `.env`:

```text
/opt/sisoc/SISOC/.env.pre_http_tmp_20260519_161828
```

Overrides temporales activos:

```dotenv
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_CSRF_TRUSTED_ORIGINS=http://10.1.135.170,https://sisoc.secretarianaf.gob.ar
DOMINIO=http://10.1.135.170/
```

Se recrearon `django`, `bulk_credentials_worker` y `ciudadanos_import_worker` con:

```bash
docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml up -d --force-recreate django bulk_credentials_worker ciudadanos_import_worker
```

Validacion posterior:

- `http://10.1.135.170/` devuelve `200 OK`.
- `http://10.1.135.170/health/` devuelve `200 OK`.
- La cookie CSRF queda sin flag `Secure`, requerido para operar temporalmente por HTTP.
- El scan de logs de `django`, `bulk_credentials_worker` y `ciudadanos_import_worker` no mostro tracebacks ni errores nuevos.

Reversa obligatoria al implementar TLS:

1. Quitar los overrides temporales `DJANGO_SECURE_*`.
2. Restaurar `DOMINIO=https://sisoc.secretarianaf.gob.ar/`.
3. Dejar `DJANGO_CSRF_TRUSTED_ORIGINS=https://sisoc.secretarianaf.gob.ar` salvo que haya otros origenes aprobados.
4. Recrear los tres servicios de app.
5. Validar `https://sisoc.secretarianaf.gob.ar/health/` con `200 OK`.

## Operacion rapida

Reiniciar app:

```bash
cd /opt/sisoc/SISOC
docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml restart django bulk_credentials_worker ciudadanos_import_worker
```

Revisar estado:

```bash
cd /opt/sisoc/SISOC
docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml ps
```

Revisar logs:

```bash
cd /opt/sisoc/SISOC
docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml logs -f --tail 200 django bulk_credentials_worker ciudadanos_import_worker
sudo tail -f /var/log/nginx/sisoc-prd.error.log
```

Confirmacion de seguridad operativa: no se uso `docker compose down -v`, no se borraron volumenes MySQL y no se borro `/opt/sisoc-mysql/data`.
