# Setup local

## Requisitos
- Docker y Docker Compose instalados; Python 3.11+ solo si se corre fuera de contenedores; VSCode recomendado. Evidencia: README.md:36-40.

## Variables de entorno
- Copiar `.env.example` a `.env` y completar Django, base de datos, puertos y claves de GESTIONAR/RENAPER. Evidencia: .env.example:1-114.
- Los archivos `.env.qa`, `.env.homologacion` y `.env.prod` quedan trackeados en git como bases saneadas de referencia; no deben llevar credenciales ni datos reales.
- En deploys versionados tambien se usa el `.env` normal del servidor/checkout; el valor de `ENVIRONMENT` dentro de ese archivo define si el runtime queda en `qa`, `homologacion` o `prd`.

## Despliegue local con Docker Compose
- `docker-compose.yml` queda reservado para desarrollo/local.
- Colocar opcionalmente un dump en `docker/mysql/local-dump.sql`, luego levantar servicios con `docker compose up` y acceder en `http://localhost:8001` (default de `DOCKER_DJANGO_PORT_FORWARD`). Evidencia: docker-compose.yml:1-34 y .env.example:1-114.
- Servicios definidos: contenedor `mysql` y `django`, con volumenes y puertos parametrizados. Evidencia: docker-compose.yml:1-34.

## Despliegue por entorno
- Compose base versionado: `docker-compose.deploy.yml` con el servicio `django` y `env_file: .env`.
- Override versionado adicional hoy presente en el repo:
  - `docker-compose.produccion.yml`
- Los archivos `.env.qa`, `.env.homologacion` y `.env.prod` quedan trackeados en git como bases saneadas de referencia; no deben llevar credenciales ni datos reales.
- En deploys versionados se usa el `.env` normal del servidor/checkout; `ENVIRONMENT` define si el runtime queda en `qa`, `homologacion` o `prd`.
- Comandos de referencia:
  - Base comun: `docker compose -f docker-compose.deploy.yml up -d --build`
  - Produccion con worker extra: `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml up -d --build`
- En produccion, `docker-compose.produccion.yml` agrega `bulk_credentials_worker` con `DJANGO_SERVICE_ROLE=bulk_credentials_worker` para que el worker quede levantado junto con la aplicacion web.
- En los deploys versionados no se levanta `mysql` dentro de Compose; la base se resuelve por variables `DATABASE_*` definidas en el `.env` del host.

## Actualizacion operativa desde Git
- Script versionado: `scripts/operacion/deploy_refresh.sh`.
- Uso recomendado desde la raiz del checkout del servidor:
  - `bash scripts/operacion/deploy_refresh.sh --dry-run`
  - `bash scripts/operacion/deploy_refresh.sh`
- Si el servidor tambien tiene `SISOC-Mobile` como checkout hermano en `../SISOC-Mobile`, usar:
  - `bash scripts/operacion/deploy_refresh.sh --with-mobile --dry-run`
  - `bash scripts/operacion/deploy_refresh.sh --with-mobile`
- Si `SISOC-Mobile` esta en otra ruta, indicar el path:
  - `bash scripts/operacion/deploy_refresh.sh --with-mobile --mobile-dir /srv/sisoc/SISOC-Mobile`
- El script lee `ENVIRONMENT` desde `.env` y elige automaticamente:
  - `dev|local|development`: `docker-compose.yml`
  - `qa|homologacion`: `docker-compose.deploy.yml`
  - `prd|prod|production`: `docker-compose.deploy.yml` + `docker-compose.produccion.yml`
- Con `--with-mobile`, SISOC delega el deploy mobile ejecutando `bash ../SISOC-Mobile/scripts/operacion/deploy_refresh.sh` y le reenvia las opciones compatibles (`--dry-run`, `--yes`, `--volumes`, `--skip-pull`, `--allow-dirty`, `--allow-branch-mismatch`).
- Antes de actualizar mobile, valida que `origin` sea
  `dsocial118/SISOC-Mobile` y normaliza las variantes SSH conocidas a
  `https://github.com/dsocial118/SISOC-Mobile.git`. Un origin distinto bloquea
  el deploy antes de bajar contenedores.
- Flujo ejecutado:
  1. valida `.env`, branch esperada y compose;
  2. ejecuta `git fetch origin --prune`;
  3. si corresponde, valida tambien el checkout mobile;
  4. baja el stack con `docker compose down --remove-orphans`;
  5. actualiza la branch actual con `git pull --ff-only`;
  6. levanta con `docker compose up -d --build`;
  7. muestra `docker compose ps`.
- Por seguridad, no borra volumenes por defecto. Si se necesita un apagado con `--volumes`, usar `bash scripts/operacion/deploy_refresh.sh --volumes` y confirmar explicitamente. En entornos con MySQL local, `--volumes` puede borrar datos persistentes.
- Si el servidor usa una branch distinta a la esperada para el `ENVIRONMENT`, corregir la branch antes de desplegar o usar `--allow-branch-mismatch` solo con una decision operativa explicita.

## NGINX de produccion
- Configuracion de referencia: `docs/operacion/nginx/sisoc-produccion.conf`.
- La topologia esperada es Django en `127.0.0.1:8001`, SISOC-Mobile en `127.0.0.1:8080` y la app mobile publicada bajo `/mobile/`.
- Antes de recargar NGINX en el servidor, validar con `sudo nginx -t`.

## Flujo de arranque en el contenedor Django
- Con `DJANGO_SERVICE_ROLE=web` (default), el entrypoint ejecuta `makemigrations` (segun `RUN_MAKEMIGRATIONS_ON_START`), `migrate`, `load_fixtures`, `create_test_users` y `create_groups`; luego levanta Gunicorn en QA/Homologacion/PRD y runserver en DEV. Evidencia: docker/django/entrypoint.py:78-111 y docker/django/entrypoint.py:129-159.
- Con `DJANGO_SERVICE_ROLE=bulk_credentials_worker`, el contenedor no levanta servidor web ni corre el flujo de migraciones/fixtures; ejecuta `manage.py process_bulk_credentials_jobs`. Evidencia: docker/django/entrypoint.py:114-127.

## Debug y desarrollo
- Debug recomendado en VSCode con la configuracion "Django in Docker"; levantar servicios antes con `docker compose up`. Evidencia: README.md:66-68.

## Tests automaticos
- Ejecutar `docker compose exec django pytest -n auto` desde el host. Evidencia: README.md:107-112 y AGENTS.md:5-8.
