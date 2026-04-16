# SISOC - Infra Readme

> Estado: **Draft operativo**
>
> Alcance: infraestructura y operacion (sin supuestos fuera de evidencia).

## Snapshot rapido

| Tema                     | Estado                                                         |
| ------------------------ | -------------------------------------------------------------- |
| Branch de despliegue QA  | `development`                                                  |
| Branch homologacion      | `homologacion`                                                 |
| Branch de despliegue PRD | `main`                                                         |
| Hosting                  | Self-hosted + NGINX interno                                    |
| Base de datos            | MySQL                                                          |
| Compose de deploy        | Base `docker-compose.deploy.yml` + override versionado por entorno |
| Cola asincrona           | No Celery/Kafka (threads + ThreadPoolExecutor)                 |
| Secret manager           | No (operacion actual con `.env`)                               |

## 1. Purpose

- Backoffice Django para gestion de modulos sociales (comedores, relevamientos, ciudadania, admisiones, centro de familia y otros).
- Centraliza operacion interna web + API DRF con documentacion OpenAPI.
- Integra con servicios externos para sincronizacion y validacion de datos (GESTIONAR, RENAPER y SISOC Mobile).

- Casos de uso criticos:
  - Gestion de comedores y sincronizacion con GESTIONAR.
  - Registro de relevamientos y sincronizacion con GESTIONAR.
  - Operacion de modulos de ciudadania/admisiones/centro de familia.
  - Administracion de usuarios, grupos y permisos internos.

## 2. Entornos

| Entorno      | URL(s)                                 | Hosting                     | Notas                                                                                                 | Owner     |
| ------------ | -------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------- | --------- |
| qa           | http://10.80.9.15/                     | Self-hosted + NGINX interno | Deploy desde branch `development`; usa `docker-compose.deploy.yml` + `docker-compose.qa.yml`         | Tech Lead |
| homologacion | https://homologacion.sisoc.example.gov.ar/ | Self-hosted + NGINX interno | Deploy desde branch `homologacion`; entorno similar a produccion, con base externa y Sentry propio | Tech Lead |
| prd          | https://sisoc.secretarianaf.gob.ar/    | Self-hosted + NGINX interno | Deploy desde branch `main`; host app reportado `10.80.5.45`; MySQL reportado `10.80.5.22`           | Tech Lead |

## 3. Architecture (High-level)

- C4-style container list:
  - Cliente web (navegador).
  - NGINX interno (reverse proxy/edge interno).
  - Contenedor Django (Gunicorn en qa/homologacion/prd, runserver en dev).
  - MySQL (persistencia principal).
  - Memcache/LocMem (cache en memoria de la aplicacion).
  - Integraciones HTTP externas: GESTIONAR, RENAPER y SISOC Mobile.

- C4 Container Diagram (Mermaid):
![Diagrama de red SISOC](../imgs/net_diagram.png)

## 4. Networking / Edge

- Entry points (DNS/CDN/WAF/LB):
  - DNS publico para prd: `sisoc.secretarianaf.gob.ar`.
  - DNS esperado para homologacion: `homologacion.sisoc.example.gov.ar`.
  - CDN/WAF/LB: Desconocido, trabajo de infra.
  - Edge interno: NGINX.

- Puertos/protocolos de ingreso:
  - HTTP en qa y HTTPS en homologacion/prd.
  - Puerto 8001 para Django.

- Dependencias de egreso:
  - APIs GESTIONAR.
  - API RENAPER.
  - SISOC Mobile.
  - Google Maps.

- Allowed origins/CORS (if applicable):
  - CORS permitido por lista derivada de `DJANGO_ALLOWED_HOSTS`.
  - Origenes efectivos por entorno: https://api.appsheet.com y los dominios del ecosistema SISOC.

## 5. Compute / Runtime

- App runtime:
  - Python 3.11.9.
  - Django 4.2.x + DRF.
  - Gunicorn en qa/homologacion/prd; runserver en dev.

- Process model:
  - Proceso web Django.
  - `docker-compose.yml` local define `mysql` + `django`.
  - Los deploys versionados usan `docker-compose.deploy.yml` mas un override por entorno y no levantan `mysql`.
  - Jobs programados por cron del host (limpieza logs, prune Docker, hetrixtools, purge_auditlog).

- Autoscaling rules (if any):
  - UNKNOWN (no evidencia de autoscaling/orquestador en repo).

## 6. Data Stores

- Primary DB (engine, version if known):
  - MySQL 8.0 (principal).
  - Tests pueden usar SQLite in-memory.

- Cache (Memcached/Memcache):
  - Configuracion Django: LocMemCache (cache en memoria local).
  - No se usa Redis.

- Object storage:
  - No evidencia de S3/MinIO.
  - Media en filesystem local del host/contenedor.

- Backups + retention + restore test status:
  - Gestion de backups a cargo de Infra.
  - Frecuencia/retencion/ultimo restore test: UNKNOWN.

## 7. Async / Queues / Schedulers

- Asincronismo:
  - No hay Celery/Kafka en arquitectura actual; la asincronia es con threading + ThreadPoolExecutor.

- Scheduled jobs (cron):
  - Limpieza diaria de logs.
  - Docker prune semanal.
  - Agente HetrixTools cada 5 minutos.
  - Purga diaria de auditlog mayor a 180 dias.

## 8. Integrations / Third parties

| Provider    | Purpose                           | Auth method                             | Rate limits | Failure mode                                      | Notes                             |
| ----------- | --------------------------------- | --------------------------------------- | ----------- | ------------------------------------------------- | --------------------------------- |
| GESTIONAR   | Sincronizacion de instancias      | `applicationAccessKey` (header)         | 0           | Reintentos limitados/errores logueados            | Endpoints por variables de entorno |
| RENAPER     | Validacion/consulta de ciudadanos | Usuario/contrasena por variables        | UNKNOWN     | Timeout/error de API externa afecta validacion    | Configurado en settings/env       |
| Google Maps | Funcionalidad geografica opcional | API key                                 | 0           | Degradacion de features de mapas                  | Clave opcional                    |
| SISOC Mobile| Aplicacion de campo para SISOC    | API key                                 | 0           | Reintentos limitados/errores logueados            | Solo usuarios autenticados        |

## 9. Deploy / Release / Rollback

- How deploys happen (CI/CD):
  - CI ejecuta lint/tests en PR/push (`development`/`main`).
  - Los PRs contra `main` ejecutan ademas un sanity check de release (`check --deploy`, validacion de schema OpenAPI y `collectstatic`) para detectar fallas de despliegue antes del merge.
  - Deploy a qa/homologacion/prd es manual por Tech Lead.
  - Politica de release documentada: flujo `development` -> `homologacion` -> `main`, con validacion previa antes de promover a prd.

- Migration strategy:
  - Migraciones Django en arranque del contenedor por entrypoint.
  - En dev puede ejecutar `makemigrations` automaticamente segun flags.

- Rollback procedure:
  - Basado en ultimo tag estable y backup de DB segun checklist.

- Module toggles (if any):
  - Flags de runtime por entorno y seguridad (`ENVIRONMENT`, `DEBUG`, CSP, arranque/migraciones).
  - `ENVIRONMENT=homologacion` hereda perfil similar a produccion para HTTPS, cookies seguras, storage, Sentry e integracion GESTIONAR.

## 10. Observability

- Logs (where, format):
  - Logging central en archivos rotativos diarios por nivel (`info`/`error`/`warning`/`critical`) + `data.log` JSON.
  - Directorio por defecto `logs/` con fallback configurable.

- Metrics (where, key dashboards):
  - Dashboards/stack de metricas: UNKNOWN.

- Traces (if any):
  - Sentry para el trackeo de errores.

- Alerts (top alerts):
  - HetrixTools para errores en el server.
  - Sentry para errores de codigo.

## 11. Security / Compliance

- Secrets management:
  - Actual: variables de entorno via archivo `.env` (sin secret manager activo).
  - Baseline recomienda migrar a secret manager en prod en el futuro.

- AuthN/AuthZ (SSO/OAuth/JWT):
  - Web: sesion Django.
  - API: TokenAuthentication + SessionAuthentication; permisos DRF por defecto autenticado.
  - API keys disponibles para integraciones.

- Least privilege / network policies:
  - Hardening de Django por entorno (HSTS/SSL redirect/cookies seguras/CSP).
  - Politicas de red formales (segmentacion, SG/NACL, egress allowlist): nada implementado.
