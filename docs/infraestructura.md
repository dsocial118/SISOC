# SISOC — Infra Readme

> Estado: **Draft operativo**
>
> Alcance: infraestructura y operación (sin supuestos fuera de evidencia).

## Questionnaire (pendiente para completar UNKNOWN)

| Dominio          | Pregunta                                                              |
| ---------------- | --------------------------------------------------------------------- |
| Runtime/Hosting  | ¿Qué región/datacenter se usa para qa y prd?                          |
| Networking/Edge  | ¿Hay WAF/LB explícito delante de NGINX interno? Si sí, ¿cuál?         |
| Data Stores      | ¿Frecuencia, retención y prueba de restore de backups (DB y media)?   |
| Observability    | ¿Qué alertas top están activas hoy y en qué herramienta?              |
| Security/Secrets | ¿Plan y fecha objetivo para migrar de `.env` a un secret manager?     |
| Ownership/SLOs   | ¿SLO/SLI definidos (disponibilidad, latencia, MTTR) y on-call formal? |

## Snapshot rápido

| Tema                     | Estado                                         |
| ------------------------ | ---------------------------------------------- |
| Branch de despliegue QA  | `development`                                  |
| Branch de despliegue PRD | `main`                                         |
| Hosting                  | Self-hosted + NGINX interno                    |
| Base de datos            | MySQL                                          |
| Cola asíncrona           | No Celery/Kafka (threads + ThreadPoolExecutor) |
| Secret manager           | UNKNOWN (operación actual con `.env`)          |

## 1. Purpose

- Backoffice Django para gestión de módulos sociales (comedores, relevamientos, ciudadanía, admisiones, centro de familia y otros).
- Centraliza operación interna web + API DRF con documentación OpenAPI.
- Integra con servicios externos para sincronización y validación de datos.

- Critical user journeys:
  - Gestión de comedores y sincronización con GESTIONAR.
  - Registro de relevamientos y envío a GESTIONAR.
  - Operación de módulos de ciudadanía/admisiones/centro de familia.
  - Administración de usuarios, grupos y permisos internos.
  - Monitoreo básico de disponibilidad vía endpoint de healthcheck.

## 2. Environments

| Environment | URL(s)                              | Region  | Hosting                     | Notes                                                                                     | Owner     |
| ----------- | ----------------------------------- | ------- | --------------------------- | ----------------------------------------------------------------------------------------- | --------- |
| qa          | http://10.80.9.15/                  | UNKNOWN | Self-hosted + NGINX interno | Deploy desde branch `development`; MySQL reportado en `10.80.9.15`                        | Tech Lead |
| prd         | https://sisoc.secretarianaf.gob.ar/ | UNKNOWN | Self-hosted + NGINX interno | Deploy desde branch `main`; host app reportado `10.80.5.45`; MySQL reportado `10.80.5.22` | Tech Lead |

## 3. Architecture (High-level)

- C4-style container list:
  - Cliente web (navegador).
  - NGINX interno (reverse proxy/edge interno).
  - Contenedor Django (Gunicorn en qa/prd, runserver en dev).
  - MySQL (persistencia principal).
  - Redis (servicio levantado junto a Django según operación actual).
  - Integraciones HTTP externas: GESTIONAR, RENAPER (y Google Maps opcional por key).

- Data flow for critical paths:
  - Login/uso web: Cliente → NGINX → Django (middleware/auth) → MySQL → respuesta.
  - Alta/edición de comedor: Cliente/API → Django → persistencia MySQL → hilo ThreadPoolExecutor → POST a GESTIONAR.
  - Relevamiento: Cliente/API → Django → MySQL → hilo ThreadPoolExecutor → POST a GESTIONAR → update de `docPDF`.

- Diagram placeholders:
  - [ ] C4 Container Diagram
  - [ ] Edge/Network Diagram

## 4. Networking / Edge

- Entry points (DNS/CDN/WAF/LB):
  - DNS público confirmado para prd: `sisoc.secretarianaf.gob.ar`.
  - CDN/WAF/LB: UNKNOWN.
  - Edge interno confirmado: NGINX interno.

- Ingress ports/protocols:
  - HTTP en qa y HTTPS en prd observables por URL.
  - Puertos exactos de edge externo: UNKNOWN.

- Egress dependencies:
  - APIs GESTIONAR (múltiples endpoints de sincronización).
  - API RENAPER.
  - Google Maps (opcional por API key).

- Allowed origins/CORS (if applicable):
  - CORS permitido por lista derivada de `DJANGO_ALLOWED_HOSTS`.
  - Orígenes efectivos por entorno: UNKNOWN (dependen de variables runtime).

## 5. Compute / Runtime

- App runtime:
  - Python 3.11.9.
  - Django 4.2.x + DRF.
  - Gunicorn en qa/prd; runserver en dev.

- Process model:
  - Proceso web Django.
  - MySQL y Django definidos en compose local.
  - Jobs programados por cron del host (limpieza logs, prune Docker, hetrixtools, purge_auditlog).

- Autoscaling rules (if any):
  - UNKNOWN (no evidencia de autoscaling/orquestador en repo).

## 6. Data Stores

- Primary DB (engine, version if known):
  - MySQL 8.0 (principal).
  - Tests pueden usar SQLite in-memory.

- Cache (Redis/Memcached):
  - Configuración Django: LocMemCache.
  - Redis: operativo reportado por infraestructura; uso funcional exacto en app UNKNOWN.

- Object storage:
  - No evidencia de S3/MinIO.
  - Media en filesystem local del host/contenedor (reportado).

- Backups + retention + restore test status:
  - Gestión de backups a cargo de Infra.
  - Frecuencia/retención/último restore test: UNKNOWN.

## 7. Async / Queues / Schedulers

- Celery/RQ/Sidekiq/etc:
  - No hay Celery/Kafka en arquitectura actual.

- Broker + result backend:
  - No aplica (asincronía con threading + ThreadPoolExecutor).

- Scheduled jobs (cron/beat):
  - Limpieza diaria de logs.
  - Docker prune semanal.
  - Agente HetrixTools cada 5 minutos.
  - Purga diaria de auditlog mayor a 180 días.

## 8. Integrations / Third parties

| Provider       | Purpose                                                            | Auth method                                 | Rate limits  | Failure mode                                                              | Notes                                   |
| -------------- | ------------------------------------------------------------------ | ------------------------------------------- | ------------ | ------------------------------------------------------------------------- | --------------------------------------- |
| GESTIONAR      | Sincronización de comedores/relevamientos/observaciones/referentes | `applicationAccessKey` (header)             | UNKNOWN      | Reintentos limitados/errores logueados; posible desincronización temporal | Endpoints por variables de entorno      |
| RENAPER        | Validación/consulta de datos ciudadanos                            | Usuario/contraseña por variables de entorno | UNKNOWN      | Timeout/error de API externa afecta validación                            | Configurado en settings/env             |
| Google Maps    | Funcionalidad geográfica opcional                                  | API key                                     | UNKNOWN      | Degradación de features de mapas                                          | Clave opcional                          |
| GitHub Actions | CI de lint/tests                                                   | GitHub repo/workflow permissions            | Según GitHub | Bloqueo de merge por checks fallidos                                      | No despliega automáticamente a entornos |

## 9. Deploy / Release / Rollback

- How deploys happen (CI/CD):
  - CI ejecuta lint/tests en PR/push (`development`/`main`).
  - Deploy a qa/prd es manual por Tech Lead.
  - Política de release documentada: flujo `development` → freeze/tag → validación QA → merge a `main` para prd.

- Migration strategy:
  - Migraciones Django en arranque del contenedor por entrypoint.
  - En dev puede ejecutar `makemigrations` automáticamente según flags.

- Rollback procedure:
  - Basado en último tag estable y backup de DB según checklist.
  - Runbook técnico detallado de rollback: UNKNOWN.

- Feature flags / module toggles (if any):
  - Flags de runtime por entorno y seguridad (`ENVIRONMENT`, `DEBUG`, CSP, arranque/migraciones).
  - Sistema formal de feature flags: UNKNOWN.

## 10. Observability

- Logs (where, format):
  - Logging central en archivos rotativos diarios por nivel (`info`/`error`/`warning`/`critical`) + `data.log` JSON.
  - Directorio por defecto `logs/` con fallback configurable.

- Metrics (where, key dashboards):
  - Dashboards/stack de métricas: UNKNOWN.

- Traces (if any):
  - No evidencia de tracing distribuido activo.

- Alerts (top alerts):
  - HetrixTools (agente cron) presente.
  - Alertas top y umbrales activos: UNKNOWN.
  - Sentry en implementación (aún no confirmado como activo en producción).

## 11. Security / Compliance

- Secrets management:
  - Actual: variables de entorno vía archivo `.env` (sin secret manager activo, según operación actual).
  - Baseline recomienda migrar a secret manager en prod.

- Data classification (PII?) — if unknown, mark UNKNOWN:
  - UNKNOWN (alta probabilidad de PII por dominio ciudadanos/RENAPER; falta clasificación formal documentada).

- AuthN/AuthZ (SSO/OAuth/JWT):
  - Web: sesión Django.
  - API: TokenAuthentication + SessionAuthentication; permisos DRF por defecto autenticado.
  - API keys disponibles para integraciones.

- Least privilege / network policies:
  - Hardening de Django por entorno (HSTS/SSL redirect/cookies seguras/CSP).
  - Políticas de red formales (segmentación, SG/NACL, egress allowlist): UNKNOWN.

## 12. Active Modules & Planned Activation

| Module                 | Status (ON/OFF/Deprecated) | Flag                          | Owner     | Dependencies            | Infra impact | Notes                      |
| ---------------------- | -------------------------- | ----------------------------- | --------- | ----------------------- | ------------ | -------------------------- |
| Core Django web/API    | ON                         | `ENVIRONMENT`, `DJANGO_DEBUG` | Tech Lead | MySQL, NGINX            | Alto         | Servicio principal         |
| Comedores sync         | ON                         | `GESTIONAR_*`                 | Tech Lead | GESTIONAR API           | Medio        | Hilos + HTTP externo       |
| Relevamientos sync     | ON                         | `GESTIONAR_*`                 | Tech Lead | GESTIONAR API           | Medio        | Hilos + HTTP externo       |
| RENAPER integration    | ON                         | `RENAPER_*`                   | Tech Lead | RENAPER API             | Medio        | Dependencia externa        |
| Audittrail + purge job | ON                         | N/A                           | Tech Lead | MySQL, cron             | Bajo/Medio   | Purga diaria 180 días      |
| Healthcheck endpoint   | ON                         | N/A                           | Tech Lead | Django                  | Bajo         | `GET /health/`             |
| Sentry monitoring      | OFF (planned)              | UNKNOWN                       | Tech Lead | Sentry SaaS/self-hosted | Bajo/Medio   | Declarado “próximo sprint” |

## 13. Priorities (Infra-relevant roadmap)

- Now (0–2 weeks):
  - Definir y documentar backup/restore DB+media. **Impacto:** Alto. **Riesgo:** Alto. **Dependencia:** Infra. **DoD:** runbook versionado + evidencia de restore exitoso.
  - Formalizar matriz de entornos (qa/prd) con región, DNS, LB/WAF y owner operativo. **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Infra + Tech Lead. **DoD:** tabla cerrada sin UNKNOWN críticos.
  - Establecer política de deploy manual con checklist único (qa desde `development`, prd desde `main`). **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Tech Lead. **DoD:** procedimiento reproducible validado en 1 release.

- Next (2–6 weeks):
  - Activar Sentry en qa y luego prd con alertas mínimas. **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Infra + App team. **DoD:** proyecto activo, DSN por entorno y 3 alertas base operativas.
  - Migrar secretos críticos de `.env` a secret manager. **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Infra. **DoD:** secretos fuera de archivos locales en qa/prd.
  - Definir SLI/SLO y alertas asociadas (disponibilidad y error rate). **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Owner + Infra. **DoD:** objetivos publicados y monitoreados.

- Later (6–12 weeks):
  - Endurecer edge con WAF/LB documentado y reglas mínimas. **Impacto:** Medio/Alto. **Riesgo:** Medio. **Dependencia:** Infra. **DoD:** arquitectura edge documentada y validada.
  - Revisar estrategia de asincronía para integraciones externas (capacidad/reintentos). **Impacto:** Medio. **Riesgo:** Medio. **Dependencia:** Equipo backend. **DoD:** límites de concurrencia y política de reintentos formalizados.
  - Consolidar observabilidad (logs+métricas+alertas) en un tablero operativo único. **Impacto:** Alto. **Riesgo:** Medio. **Dependencia:** Infra + App team. **DoD:** dashboard único con runbook de respuesta.

## 14. Open Questions / Unknowns

- Región/datacenter de qa y prd — responde Infra.
- Existencia/config de WAF/LB delante de NGINX — responde Infra.
- Frecuencia/retención/último restore test de backups — responde Infra.
- Alertas activas actuales y umbrales — responde Infra/Tech Lead.
- Clasificación formal de datos (PII) y controles de cumplimiento — responde Seguridad/Producto.
- SLO/SLI y guardias on-call formales — responde Tech Lead/Operaciones.

---

## Sources (audit trail)

- README.md
- docs/operaciones.md
- docs/arquitectura.md
- docs/panorama.md
- docs/SECURITY_BASELINE.md
- docker-compose.yml
- docker/django/Dockerfile
- docker/django/entrypoint.py
- config/settings.py
- .env.example
- .github/workflows/tests.yml
- .github/workflows/lint.yml
- scripts/crontab
- healthcheck/urls.py
- healthcheck/views.py
- requirements/base.txt
- appspec.yml
