# Setup local

## Requisitos
- Docker y Docker Compose instalados; Python 3.11+ solo si se corre fuera de contenedores; VSCode recomendado. Evidencia: README.md:36-40.

## Variables de entorno
- Copiar `.env.example` a `.env` y completar Django, base de datos, puertos y claves de GESTIONAR/RENAPER. Evidencia: .env.example:1-51.
- En deploys versionados tambien se usa el `.env` normal del servidor/checkout; el valor de `ENVIRONMENT` dentro de ese archivo define si el runtime queda en `qa`, `homologacion` o `prd`.

## Despliegue local con Docker Compose
- `docker-compose.yml` queda reservado para desarrollo/local.
- Colocar opcionalmente un dump en `docker/mysql/local-dump.sql`, luego levantar servicios con `docker compose up` y acceder en `http://localhost:8000`. Evidencia: README.md:45-64.
- Servicios definidos: contenedor `mysql` y `django`, con volumenes y puertos parametrizados. Evidencia: docker-compose.yml:1-34.

## Despliegue por entorno
- Compose base compartido: `docker-compose.deploy.yml` con solo el servicio `django` y `env_file: .env`.
- Overrides versionados:
  - `docker-compose.qa.yml`
  - `docker-compose.homologacion.yml`
  - `docker-compose.produccion.yml`
- Comandos de referencia:
  - `docker compose -f docker-compose.deploy.yml -f docker-compose.qa.yml up -d --build`
  - `docker compose -f docker-compose.deploy.yml -f docker-compose.homologacion.yml up -d --build`
  - `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml up -d --build`
- En los deploys versionados no se levanta `mysql` dentro de Compose; la base se resuelve por variables `DATABASE_*` definidas en el `.env` del host.

## Flujo de arranque en el contenedor Django
- Al iniciar, el entrypoint ejecuta `makemigrations`, `migrate`, carga fixtures (`load_fixtures`) y crea usuarios/grupos de prueba (`create_test_users`, `create_groups`); usa Gunicorn en QA/Homologacion/PRD y runserver en DEV. Evidencia: docker/django/entrypoint.py:55-95.

## Debug y desarrollo
- Debug recomendado en VSCode con la configuracion "Django in Docker"; levantar servicios antes con `docker compose up`. Evidencia: README.md:66-68.

## Tests automaticos
- Ejecutar `docker compose exec django pytest -n auto` desde el host. Evidencia: README.md:107-112 y AGENTS.md:5-8.
