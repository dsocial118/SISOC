# Arquitectura

## 1) Diagrama textual (ASCII)
```
           ┌───────────────┐
           │  Cliente web  │
           └───────┬───────┘
                   │ HTTP (auth Django)
            ┌──────▼───────┐
            │   Django     │
            │(views/DRF)   │
            └──────┬───────┘
   ┌────────────┬──┴──┬────────────┐
   │Middleware  │URLs │ Templates  │
   └──────┬─────┴─────┴──────┬─────┘
          │                  │
   ┌──────▼──────┐    ┌──────▼──────┐
   │  Services   │    │ Serializers │
   └──────┬──────┘    └──────┬──────┘
          │                  │
      ┌───▼───┐          ┌───▼───┐
      │ Models│          │ Auth  │
      └───┬───┘          └───┬───┘
          │                  │
   ┌──────▼──────┐     ┌─────▼─────┐
   │  MySQL      │     │  Cache    │
   └─────────────┘     │ (LocMem)  │
                        └──────────┘

      ┌────────────────────────────────────────┐
      │   Servicios externos (HTTP, async)     │
      │ - GESTIONAR (comedores, relevamientos) │
      │ - RENAPER (consulta ciudadanía)        │
      │ - Google Maps API key (opcional)       │
      └────────────────────────────────────────┘
```
Evidencia: config/settings.py:42-389; config/urls.py:12-44; comedores/tasks.py:1-249; relevamientos/tasks.py:1-144; centrodefamilia/services/consulta_renaper.py:13-170; docker-compose.yml:1-34.

## 2) Capas existentes
- Presentación: vistas Django y DRF (urls en `config/urls.py`), plantillas en `templates/` y apps propias. Evidencia: config/urls.py:12-44; config/settings.py:105-120.
- Middleware: seguridad, sesiones, CORS, CSRF, autenticación, auditlog, mensajes, XFrame, XSS custom, threadlocals; en DEBUG se agregan debug_toolbar y silk. Evidencia: config/settings.py:85-99,359-366.
- Servicios/negocio: servicios en apps (ej. `comedores/services`, `centrodefamilia/services`), sincronización con GESTIONAR/RENAPER en `tasks.py` y `consulta_renaper.py`. Evidencia: comedores/tasks.py:1-249; centrodefamilia/services/consulta_renaper.py:13-170.
- Dominio/persistencia: modelos en cada app; DB configurada a MySQL. Evidencia: config/settings.py:153-168; apps listadas en config/settings.py:42-83.
- Serialización/API schema: DRF + drf-spectacular. Evidencia: config/settings.py:195-234.

## 3) Flujo request → response
- Entrada HTTP → middleware chain (security, session, CORS, common, CSRF, auth, auditlog, messages, clickjacking, admindocs, XSSProtectionMiddleware, ThreadLocalMiddleware; en DEBUG: debug_toolbar, silk) → URL routing (`config/urls.py`) → views/templates o DRF views → respuesta. Evidencia: config/settings.py:85-99,359-366; config/urls.py:12-44.
- Autenticación: usa `django.contrib.auth` con `LOGIN_URL`/redirects y DRF por defecto exige `IsAuthenticated`. Evidencia: config/settings.py:130-135,195-203; config/urls.py:15.
- Static/media: servidos vía `staticfiles_urlpatterns` y `static` en desarrollo. Evidencia: config/urls.py:50-51; config/settings.py:122-128.

## 4) Asincronía
- No hay Celery/Kafka. Asincronía mediante hilos (`threading.Thread` + `ThreadPoolExecutor`) para llamadas HTTP a GESTIONAR en comedores/relevamientos. Evidencia: comedores/tasks.py:1-249; relevamientos/tasks.py:1-144.
- Cron programados externos: purga auditlog y limpieza de logs (scripts/crontab). Evidencia: scripts/crontab:2-5; audittrail/management/commands/purge_auditlog.py:1-38; scripts/borrar_logs.py:1-43.

## 5) Almacenamiento
- Base de datos: MySQL (principal); pytest usa SQLite en memoria. Evidencia: config/settings.py:153-174; docker-compose.yml:1-19.
- Cache: `LocMemCache` (no compartida entre instancias). Evidencia: config/settings.py:175-189.
- Archivos estáticos/media: filesystem (`STATIC_ROOT`, `MEDIA_ROOT`). Evidencia: config/settings.py:122-128.
- No hay search engine declarado.

## 6) Configuración por entorno
- Variable `ENVIRONMENT` (dev|qa|prd) y `DJANGO_DEBUG` controlan toggles; en prd se activa HSTS, SSL redirect, cookies seguras y ManifestStaticFilesStorage; en dev se habilitan toolbars. Evidencia: config/settings.py:12-15,136-140,359-388.
- Entrypoint Docker usa `.env` y ejecuta migraciones/fixtures al iniciar; Gunicorn en QA/PRD, runserver en DEV. Evidencia: docker/django/entrypoint.py:55-95.
- Variables de entorno definidas en `.env.example` (DB, GESTIONAR, RENAPER, puertos, dominio, Gunicorn). Evidencia: .env.example:1-51.

## 7) Puntos de extensión
- Signals en varias apps (duplas, users) y auditlog middleware; management commands extensibles por app. Evidencia: users/management/commands/*.py; comedores/management/commands/*.py; relevamientos/management/commands/*.py; duplas/signals.py:1-40; auditlog middleware en config/settings.py:92-94.
- Middleware propios: `config.middlewares.xss_protection.XSSProtectionMiddleware`, `config.middlewares.threadlocals.ThreadLocalMiddleware`. Evidencia: config/settings.py:97-99.
- API schema vía drf-spectacular; extensible con componentes y enums. Evidencia: config/settings.py:195-234.
