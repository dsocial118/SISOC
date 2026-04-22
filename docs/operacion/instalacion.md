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

## Flujo de arranque en el contenedor Django
- Con `DJANGO_SERVICE_ROLE=web` (default), el entrypoint ejecuta `makemigrations` (segun `RUN_MAKEMIGRATIONS_ON_START`), `migrate`, `load_fixtures`, `create_test_users` y `create_groups`; luego levanta Gunicorn en QA/Homologacion/PRD y runserver en DEV. Evidencia: docker/django/entrypoint.py:78-111 y docker/django/entrypoint.py:129-159.
- Con `DJANGO_SERVICE_ROLE=bulk_credentials_worker`, el contenedor no levanta servidor web ni corre el flujo de migraciones/fixtures; ejecuta `manage.py process_bulk_credentials_jobs`. Evidencia: docker/django/entrypoint.py:114-127.

## Debug y desarrollo
- Debug recomendado en VSCode con la configuracion "Django in Docker"; levantar servicios antes con `docker compose up`. Evidencia: README.md:66-68.

## Tests automaticos
- Ejecutar `docker compose exec django pytest -n auto` desde el host. Evidencia: README.md:107-112 y AGENTS.md:5-8.
