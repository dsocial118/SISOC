# Entornos de deploy con homologacion

Fecha: 2026-04-07

## Que cambio

- Se separo el Compose local del Compose de deploy.
- Se agrego un compose base de deploy (`docker-compose.deploy.yml`) y tres overrides explicitos:
  - `docker-compose.qa.yml`
  - `docker-compose.homologacion.yml`
  - `docker-compose.produccion.yml`
- Se agrego `.env.homologacion` para el nuevo entorno deploy-like.
- `config/settings.py` ahora soporta `ENVIRONMENT=homologacion`.
- Homologacion pasa a comportarse como un entorno similar a produccion para:
  - esquema HTTPS por defecto
  - defaults de conexion persistente a DB
  - cookies seguras y `SECURE_SSL_REDIRECT`
  - storage de estaticos con `ManifestStaticFilesStorage`
  - disponibilidad de Sentry
  - integracion GESTIONAR habilitada

## Decision principal

Se mantuvo `docker-compose.yml` exclusivamente para desarrollo/local porque es el unico caso en el repo donde tiene sentido levantar `mysql` junto con `django`.

Para deploys se eligio un esquema base + overrides por entorno para evitar drift entre QA, homologacion y produccion, sin duplicar toda la definicion del servicio `django`.

## Impacto operativo

- QA sigue siendo un entorno no productivo y no hereda automaticamente todo el hardening de produccion.
- Homologacion queda mas cerca de produccion que de QA.
- Los deploys versionados ya no asumen `mysql` dentro de Compose; la base se resuelve por `DATABASE_*`.
- Sentry distingue `sisoc-qa`, `sisoc-homologacion` y `sisoc-prd`.

## Validacion esperada

- `docker compose -f docker-compose.deploy.yml -f docker-compose.qa.yml config -q`
- `docker compose -f docker-compose.deploy.yml -f docker-compose.homologacion.yml config -q`
- `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml config -q`
- `pytest -q tests/test_settings_env_parsing.py tests/test_docker_entrypoint_unit.py sentry/tests.py tests/test_users_auth_flows.py -k "homologacion or deploy or password_reset_link"`
